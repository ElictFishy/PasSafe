"""Le coffre : les entrées en mémoire, le fichier chiffré sur le disque.

Le fichier enregistré ne contient que les paramètres de dérivation et le bloc
chiffré. La liste des entrées n'existe en clair qu'en mémoire, et seulement
pendant que le coffre est déverrouillé.
"""

import json
import os
import time
import uuid

from utils.crypto import (
    KDF_ITERATIONS,
    KDF_NAME,
    InvalidMasterPassword,
    decrypt,
    derive_key,
    encrypt,
    new_salt,
)

VAULT_VERSION = 1
VAULT_FILENAME = "passafe.vault"

# Le mot de passe maître est le seul secret qui protège le coffre : en dessous
# de cette longueur, le ralentissement apporté par PBKDF2 ne suffit plus.
MIN_MASTER_LENGTH = 8


class VaultError(Exception):
    """Opération impossible dans l'état actuel du coffre."""


class VaultLocked(VaultError):
    """Le coffre est verrouillé : aucune clé en mémoire."""


class Entry:
    """Une ligne du coffre : un service, un identifiant, un mot de passe."""

    FIELDS = ("title", "username", "password", "url", "notes")

    def __init__(
        self,
        title="",
        username="",
        password="",
        url="",
        notes="",
        id=None,
        created_at=None,
        updated_at=None,
    ):
        self.id = id or uuid.uuid4().hex
        self.title = title
        self.username = username
        self.password = password
        self.url = url
        self.notes = notes
        self.created_at = created_at or time.time()
        self.updated_at = updated_at or self.created_at

    def to_dict(self):
        data = {field: getattr(self, field) for field in self.FIELDS}
        data.update(
            id=self.id,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def matches(self, query):
        query = query.strip().lower()
        if not query:
            return True
        # Le mot de passe est volontairement exclu de la recherche : taper
        # dans le champ filtre ne doit pas permettre de deviner son contenu.
        return any(
            query in getattr(self, field).lower()
            for field in ("title", "username", "url", "notes")
        )


class Vault:
    def __init__(self, path):
        self.path = path
        self._key = None
        self._salt = None
        self._iterations = KDF_ITERATIONS
        self._entries = []

    @property
    def exists(self):
        return os.path.isfile(self.path)

    @property
    def is_locked(self):
        return self._key is None

    def create(self, master_password):
        if self.exists:
            raise VaultError("Un coffre existe déjà à cet emplacement.")
        self._check_master_password(master_password)
        self._salt = new_salt()
        self._iterations = KDF_ITERATIONS
        self._key = derive_key(master_password, self._salt, self._iterations)
        self._entries = []
        self.save()

    def unlock(self, master_password):
        """Déchiffre le fichier, ou lève InvalidMasterPassword.

        L'appel dure quelques centaines de millisecondes à cause de PBKDF2 :
        il est lancé hors du fil principal pour ne pas figer l'interface.
        """
        container = self._read_container()
        kdf = container.get("kdf", {})
        if kdf.get("name") != KDF_NAME:
            raise VaultError(
                "Dérivation de clé inconnue : %s" % kdf.get("name")
            )

        salt = bytes.fromhex(kdf["salt"])
        iterations = int(kdf["iterations"])
        key = derive_key(master_password, salt, iterations)
        payload = json.loads(decrypt(key, container["data"]).decode("utf-8"))

        self._salt = salt
        self._iterations = iterations
        self._key = key
        self._entries = [Entry.from_dict(item) for item in payload["entries"]]

    def lock(self):
        self._key = None
        self._entries = []

    def entries(self, query=""):
        self._require_key()
        found = [entry for entry in self._entries if entry.matches(query)]
        return sorted(found, key=lambda entry: entry.title.lower())

    def get(self, entry_id):
        self._require_key()
        for entry in self._entries:
            if entry.id == entry_id:
                return entry
        raise VaultError("Entrée introuvable : %s" % entry_id)

    def add(self, **fields):
        self._require_key()
        entry = Entry(**fields)
        self._entries.append(entry)
        self.save()
        return entry

    def update(self, entry_id, **fields):
        entry = self.get(entry_id)
        for name, value in fields.items():
            if name not in Entry.FIELDS:
                raise VaultError("Champ inconnu : %s" % name)
            setattr(entry, name, value)
        entry.updated_at = time.time()
        self.save()
        return entry

    def delete(self, entry_id):
        entry = self.get(entry_id)
        self._entries.remove(entry)
        self.save()

    def change_master_password(self, current_password, new_password):
        self._require_key()
        current_key = derive_key(
            current_password, self._salt, self._iterations
        )
        if current_key != self._key:
            raise InvalidMasterPassword(
                "Mot de passe maître actuel incorrect."
            )
        self._check_master_password(new_password)
        # Nouveau sel : deux coffres protégés par le même mot de passe ne
        # doivent jamais aboutir à la même clé.
        self._salt = new_salt()
        self._iterations = KDF_ITERATIONS
        self._key = derive_key(new_password, self._salt, self._iterations)
        self.save()

    def save(self):
        self._require_key()
        payload = json.dumps(
            {"entries": [entry.to_dict() for entry in self._entries]}
        ).encode("utf-8")
        container = {
            "version": VAULT_VERSION,
            "kdf": {
                "name": KDF_NAME,
                "salt": self._salt.hex(),
                "iterations": self._iterations,
            },
            "data": encrypt(self._key, payload),
        }
        self._write_container(container)

    @staticmethod
    def _check_master_password(master_password):
        if len(master_password) < MIN_MASTER_LENGTH:
            raise VaultError(
                "Le mot de passe maître doit faire au moins %d caractères."
                % MIN_MASTER_LENGTH
            )

    def _require_key(self):
        if self.is_locked:
            raise VaultLocked("Le coffre est verrouillé.")

    def _read_container(self):
        try:
            with open(self.path, encoding="utf-8") as fd:
                container = json.load(fd)
        except (OSError, ValueError) as error:
            raise VaultError("Fichier de coffre illisible.") from error
        if container.get("version") != VAULT_VERSION:
            raise VaultError(
                "Version de coffre non gérée : %s" % container.get("version")
            )
        return container

    def _write_container(self, container):
        # Écriture dans un fichier temporaire puis remplacement atomique : une
        # coupure pendant l'enregistrement ne peut pas laisser un coffre
        # tronqué, c'est-à-dire définitivement illisible.
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        temporary = self.path + ".tmp"
        with open(temporary, "w", encoding="utf-8") as fd:
            json.dump(container, fd)
            fd.flush()
            os.fsync(fd.fileno())
        os.replace(temporary, self.path)
