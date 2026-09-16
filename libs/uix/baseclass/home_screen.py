"""Écran d'ouverture : création du coffre, puis déverrouillage."""

import threading

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from config import kv_path
from utils.crypto import InvalidMasterPassword
from utils.generator import strength
from utils.vault import MIN_MASTER_LENGTH, VaultError

Builder.load_file(kv_path("home_screen.kv"))


class HomeScreen(MDScreen):
    mode = StringProperty("unlock")  # "unlock" ou "create"
    error = StringProperty("")
    busy = BooleanProperty(False)
    strength_value = NumericProperty(0)
    strength_label = StringProperty("")

    def on_pre_enter(self, *args):
        self.mode = (
            "unlock" if MDApp.get_running_app().vault.exists else "create"
        )
        self.error = ""
        self.busy = False
        self.ids.password.text = ""
        self.ids.confirm.text = ""
        self.strength_value = 0
        self.strength_label = ""

    def on_password_text(self, text):
        if self.mode != "create":
            return
        score, label = strength(text)
        self.strength_value = score * 25
        self.strength_label = label if text else ""

    def submit(self):
        if self.busy:
            return

        password = self.ids.password.text
        if self.mode == "create":
            if len(password) < MIN_MASTER_LENGTH:
                self.error = (
                    "Le mot de passe maître doit faire au moins "
                    "%d caractères." % MIN_MASTER_LENGTH
                )
                return
            if password != self.ids.confirm.text:
                self.error = "Les deux mots de passe ne correspondent pas."
                return
        elif not password:
            self.error = "Saisissez le mot de passe maître."
            return

        self.error = ""
        self.busy = True
        # La dérivation PBKDF2 dure plusieurs centaines de millisecondes :
        # lancée dans le fil principal, elle figerait l'interface.
        threading.Thread(
            target=self._open_vault, args=(password,), daemon=True
        ).start()

    def _open_vault(self, password):
        vault = MDApp.get_running_app().vault
        error = ""
        try:
            if self.mode == "create":
                vault.create(password)
            else:
                vault.unlock(password)
        except InvalidMasterPassword:
            error = "Mot de passe maître incorrect."
        except VaultError as exception:
            error = str(exception)

        Clock.schedule_once(lambda dt: self._vault_opened(error))

    def _vault_opened(self, error):
        self.busy = False
        self.error = error
        self.ids.password.text = ""
        self.ids.confirm.text = ""
        if not error:
            MDApp.get_running_app().root.goto("pass")
