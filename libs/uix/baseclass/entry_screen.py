"""Écran de fiche : création, modification et suppression d'une entrée."""

from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen

from config import kv_path
from libs.uix.components.generator import GeneratorContent
from utils import clipboard
from utils.vault import Entry

Builder.load_file(kv_path("entry_screen.kv"))


class EntryScreen(MDScreen):
    entry_id = StringProperty(None, allownone=True)
    revealed = BooleanProperty(False)
    error = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._generator_dialog = None
        self._delete_dialog = None

    def load(self, entry_id=None):
        """Remplit le formulaire, vide pour une création."""
        self.entry_id = entry_id
        self.revealed = False
        self.error = ""

        entry = None
        if entry_id:
            entry = MDApp.get_running_app().vault.get(entry_id)
        for name in Entry.FIELDS:
            self.ids[name].text = getattr(entry, name) if entry else ""

    def back(self):
        MDApp.get_running_app().root.goto("pass", direction="right")

    def save(self):
        title = self.ids.title.text.strip()
        if not title:
            self.error = "Donnez un nom à cette entrée."
            return

        vault = MDApp.get_running_app().vault
        fields = {
            "title": title,
            "username": self.ids.username.text.strip(),
            "password": self.ids.password.text,
            "url": self.ids.url.text.strip(),
            "notes": self.ids.notes.text.strip(),
        }
        if self.entry_id:
            vault.update(self.entry_id, **fields)
        else:
            vault.add(**fields)
        self.back()

    def copy_password(self):
        password = self.ids.password.text
        if not password:
            return
        clipboard.copy(password)
        MDApp.get_running_app().snack(
            "Mot de passe copié, effacé dans %d s" % clipboard.CLEAR_DELAY
        )

    def open_generator(self):
        content = GeneratorContent()
        self._generator_dialog = MDDialog(
            title="Générer un mot de passe",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="Annuler",
                    on_release=lambda *args: self._generator_dialog.dismiss(),
                ),
                MDRaisedButton(
                    text="Utiliser",
                    on_release=lambda *args: self._use_generated(content),
                ),
            ],
        )
        self._generator_dialog.open()

    def _use_generated(self, content):
        self.ids.password.text = content.password
        # Le mot de passe généré est affiché une fois : l'utilisateur doit
        # pouvoir vérifier ce qu'il enregistre avant de le valider.
        self.revealed = True
        self._generator_dialog.dismiss()

    def confirm_delete(self):
        if not self.entry_id:
            return
        self._delete_dialog = MDDialog(
            title="Supprimer cette entrée ?",
            text="Le mot de passe enregistré sera définitivement perdu.",
            buttons=[
                MDFlatButton(
                    text="Annuler",
                    on_release=lambda *args: self._delete_dialog.dismiss(),
                ),
                MDRaisedButton(
                    text="Supprimer",
                    md_bg_color=MDApp.get_running_app().theme_cls.error_color,
                    on_release=lambda *args: self._delete(),
                ),
            ],
        )
        self._delete_dialog.open()

    def _delete(self):
        MDApp.get_running_app().vault.delete(self.entry_id)
        self._delete_dialog.dismiss()
        self.back()
