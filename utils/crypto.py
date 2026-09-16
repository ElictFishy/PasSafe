"""Chiffrement du coffre : AES-256-GCM et dérivation du mot de passe maître.

Rien n'est écrit en clair sur le disque. La clé n'existe qu'en mémoire, le
temps où le coffre est déverrouillé, et n'est jamais enregistrée : le fichier
ne contient que le sel, le nombre d'itérations et les données chiffrées.
"""

import base64
import binascii
import hashlib
import os

from Crypto.Cipher import AES

KDF_NAME = "pbkdf2-sha256"

# PBKDF2 ralentit une attaque par force brute sur le fichier volé. 200 000
# itérations sont un compromis entre cette résistance et le temps de
# déverrouillage sur un téléphone d'entrée de gamme (moins d'une seconde).
KDF_ITERATIONS = 200_000

SALT_SIZE = 16
KEY_SIZE = 32  # AES-256


class CryptoError(Exception):
    """Erreur de chiffrement ou de déchiffrement."""


class InvalidMasterPassword(CryptoError):
    """Mot de passe maître refusé, ou fichier de coffre altéré."""


def new_salt():
    return os.urandom(SALT_SIZE)


def derive_key(master_password, salt, iterations=KDF_ITERATIONS):
    return hashlib.pbkdf2_hmac(
        "sha256",
        master_password.encode("utf-8"),
        salt,
        iterations,
        dklen=KEY_SIZE,
    )


def encrypt(key, plaintext):
    """Chiffre `plaintext` et renvoie les trois champs à enregistrer."""
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return {
        "nonce": _b64(cipher.nonce),
        "tag": _b64(tag),
        "ciphertext": _b64(ciphertext),
    }


def decrypt(key, payload):
    try:
        cipher = AES.new(key, AES.MODE_GCM, nonce=_unb64(payload["nonce"]))
        return cipher.decrypt_and_verify(
            _unb64(payload["ciphertext"]), _unb64(payload["tag"])
        )
    except (KeyError, TypeError, ValueError, binascii.Error) as error:
        # GCM vérifie l'intégrité : le tag ne correspond pas aussi bien pour un
        # mauvais mot de passe que pour un fichier modifié. On ne peut pas
        # distinguer les deux cas, et il vaut mieux ne pas essayer.
        raise InvalidMasterPassword(
            "Mot de passe maître incorrect ou fichier illisible."
        ) from error


def _b64(raw):
    return base64.b64encode(raw).decode("ascii")


def _unb64(text):
    return base64.b64decode(text)
