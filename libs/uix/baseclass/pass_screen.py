"""Écran du coffre déverrouillé : liste des entrées, recherche, copie."""

import threading
from functools import partial

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import IconLeftWidget, IconRightWidget
from kivymd.uix.list import TwoLineAvatarIconListItem
from kivymd.uix.screen import MDScreen

from config import kv_path
from libs.uix.components.master_password import MasterPasswordContent
from utils import clipboard
from utils.crypto import InvalidMasterPassword
from utils.vault import VaultError

Builder.load_file(kv_path("pass_screen.kv"))


class PassScreen(MDScreen):
    query = StringProperty("")
    searching = BooleanProperty(False)
    empty = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._master_dialog = None

    def on_pre_enter(self, *args):
        self.refresh()

    def on_query(self, *args):
        self.refresh()

    def toggle_search(self):
        self.searching = not self.searching
        if self.searching:
            self.ids.search.focus = True
        else:
            self.ids.search.text = ""

    def refresh(self):
        vault = MDApp.get_running_app().vault
        container = self.ids.entries
        container.clear_widgets()
        if vault.is_locked:
            return

        entries = vault.entries(self.query)
        self.empty = not entries
        for entry in entries:
            item = TwoLineAvatarIconListItem(
                text=entry.title,
                secondary_text=entry.username or "sans identifiant",
                on_release=partial(self.open_entry, entry.id),
            )
            item.add_widget(IconLeftWidget(icon="key-variant"))
            item.add_widget(
                IconRightWidget(
                    icon="content-copy",
                    on_release=partial(self.copy_password, entry.id),
                )
            )
            container.add_widget(item)

    def open_entry(self, entry_id, *args):
        MDApp.get_running_app().root.goto("entry").load(entry_id)

    def new_entry(self):
        MDApp.get_running_app().root.goto("entry").load(None)

    def copy_password(self, entry_id, *args):
        app = MDApp.get_running_app()
        clipboard.copy(app.vault.get(entry_id).password)
        app.snack(
            "Mot de passe copié, effacé dans %d s" % clipboard.CLEAR_DELAY
        )

    def open_master_password(self):
        content = MasterPasswordContent()
        self._master_dialog = MDDialog(
            title="Changer le mot de passe maître",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="Annuler",
                    on_release=lambda *args: self._master_dialog.dismiss(),
                ),
                MDRaisedButton(
                    text="Valider",
                    on_release=lambda *args: self._change_master(content),
                ),
            ],
        )
        self._master_dialog.open()

    def _change_master(self, content):
        current = content.ids.current.text
        new = content.ids.new.text
        if new != content.ids.confirm.text:
            content.error = "Les deux nouveaux mots de passe diffèrent."
            return

        content.error = ""
        # Deux dérivations PBKDF2 : la vérification de l'ancien mot de passe
        # et la clé du nouveau. Comme au déverrouillage, hors fil principal.
        threading.Thread(
            target=self._rekey, args=(current, new), daemon=True
        ).start()

    def _rekey(self, current, new):
        vault = MDApp.get_running_app().vault
        error = ""
        try:
            vault.change_master_password(current, new)
        except InvalidMasterPassword:
            error = "Mot de passe maître actuel incorrect."
        except VaultError as exception:
            error = str(exception)

        Clock.schedule_once(lambda dt: self._rekeyed(error))

    def _rekeyed(self, error):
        if error:
            self._master_dialog.content_cls.error = error
            return
        self._master_dialog.dismiss()
        MDApp.get_running_app().snack("Mot de passe maître changé.")
