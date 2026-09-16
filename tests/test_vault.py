"""Tests de la logique du coffre, sans interface.

    python -m unittest discover tests
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import generator  # NOQA: E402
from utils.crypto import InvalidMasterPassword  # NOQA: E402
from utils.vault import Vault, VaultError, VaultLocked  # NOQA: E402

MASTER = "correct-horse-battery"


class VaultTestCase(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.path = os.path.join(self.directory, "test.vault")
        self.vault = Vault(self.path)

    def tearDown(self):
        shutil.rmtree(self.directory, ignore_errors=True)

    def test_create_then_unlock(self):
        self.vault.create(MASTER)
        self.vault.add(title="GitHub", username="elict", password="s3cret")
        self.vault.lock()

        reopened = Vault(self.path)
        reopened.unlock(MASTER)
        self.assertEqual(len(reopened.entries()), 1)
        self.assertEqual(reopened.entries()[0].password, "s3cret")

    def test_wrong_master_password_is_refused(self):
        self.vault.create(MASTER)
        self.vault.lock()
        with self.assertRaises(InvalidMasterPassword):
            Vault(self.path).unlock(MASTER + "!")

    def test_nothing_readable_on_disk(self):
        self.vault.create(MASTER)
        self.vault.add(title="GitHub", username="elict", password="s3cret")

        with open(self.path, encoding="utf-8") as fd:
            raw = fd.read()
        for secret in ("GitHub", "elict", "s3cret", MASTER):
            self.assertNotIn(secret, raw)
        self.assertEqual(json.loads(raw)["kdf"]["name"], "pbkdf2-sha256")

    def test_altered_file_is_detected(self):
        self.vault.create(MASTER)
        with open(self.path, encoding="utf-8") as fd:
            container = json.load(fd)
        data = container["data"]
        # On retourne un caractère du chiffré : le tag GCM ne doit plus passer.
        first = "B" if data["ciphertext"][0] != "B" else "C"
        data["ciphertext"] = first + data["ciphertext"][1:]
        with open(self.path, "w", encoding="utf-8") as fd:
            json.dump(container, fd)

        with self.assertRaises(InvalidMasterPassword):
            Vault(self.path).unlock(MASTER)

    def test_locked_vault_refuses_everything(self):
        self.vault.create(MASTER)
        self.vault.lock()
        with self.assertRaises(VaultLocked):
            self.vault.entries()
        with self.assertRaises(VaultLocked):
            self.vault.add(title="X")

    def test_update_and_delete(self):
        self.vault.create(MASTER)
        entry = self.vault.add(title="Mail", password="a")
        self.vault.update(entry.id, password="b")
        self.assertEqual(self.vault.get(entry.id).password, "b")

        self.vault.delete(entry.id)
        self.assertEqual(self.vault.entries(), [])
        with self.assertRaises(VaultError):
            self.vault.get(entry.id)

    def test_search_ignores_passwords(self):
        self.vault.create(MASTER)
        self.vault.add(title="Mail", username="eliott", password="zeppelin")
        self.assertEqual(len(self.vault.entries("mail")), 1)
        self.assertEqual(len(self.vault.entries("eli")), 1)
        self.assertEqual(len(self.vault.entries("zeppelin")), 0)

    def test_short_master_password_is_refused(self):
        with self.assertRaises(VaultError):
            self.vault.create("court")
        self.assertFalse(self.vault.exists)

    def test_change_master_password(self):
        self.vault.create(MASTER)
        self.vault.add(title="Mail", password="a")
        with self.assertRaises(InvalidMasterPassword):
            self.vault.change_master_password("faux", "nouveau-mot-de-passe")

        with self.assertRaises(VaultError):
            self.vault.change_master_password(MASTER, "court")

        self.vault.change_master_password(MASTER, "nouveau-mot-de-passe")
        self.vault.lock()

        reopened = Vault(self.path)
        reopened.unlock("nouveau-mot-de-passe")
        self.assertEqual(reopened.entries()[0].password, "a")


class GeneratorTestCase(unittest.TestCase):
    def test_length_and_families(self):
        password = generator.generate(length=24)
        self.assertEqual(len(password), 24)
        self.assertTrue(any(c in generator.UPPERCASE for c in password))
        self.assertTrue(any(c in generator.DIGITS for c in password))
        self.assertTrue(any(c in generator.SYMBOLS for c in password))

    def test_only_lowercase(self):
        password = generator.generate(
            length=16, uppercase=False, digits=False, symbols=False
        )
        self.assertTrue(all(c in generator.LOWERCASE for c in password))

    def test_ambiguous_characters_excluded(self):
        for _ in range(20):
            password = generator.generate(length=40)
            self.assertFalse(any(c in generator.AMBIGUOUS for c in password))

    def test_strength_grows_with_length(self):
        weak, _ = generator.strength("1234")
        strong, _ = generator.strength(generator.generate(length=32))
        self.assertLess(weak, strong)


if __name__ == "__main__":
    unittest.main()
