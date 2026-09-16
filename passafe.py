import os

from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar

from config import ASSETS_DIR, fonts
from libs.uix.baseclass.root import Root
from utils import clipboard
from utils.vault import VAULT_FILENAME, Vault

ANDROID_BACK_KEY = 27


class PasSafe(MDApp):
    def __init__(self, **kwargs):
        super(PasSafe, self).__init__(**kwargs)
        Window.soft_input_mode = "below_target"
        self.title = "PasSafe"
        self.icon = os.path.join(ASSETS_DIR, "images", "logo.png")

        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Gray"
        # Sur fond sombre, un primaire trop foncé rendrait les boutons et les
        # interrupteurs invisibles : les barres de titre, elles, fixent leur
        # couleur dans les fichiers kv.
        self.theme_cls.primary_hue = "300"

        self.theme_cls.font_styles.update(fonts.font_styles)

        self.vault = None

    def build(self):
        # user_data_dir est le dossier privé de l'application : sur Android,
        # les autres applications n'y ont pas accès.
        self.vault = Vault(os.path.join(self.user_data_dir, VAULT_FILENAME))
        Window.bind(on_keyboard=self.on_keyboard)
        return Root()

    def on_start(self):
        self.root.goto("home")

    def lock(self, *args):
        """Ferme le coffre : la clé quitte la mémoire, l'écran se vide."""
        clipboard.clear_now()
        if self.vault is not None:
            self.vault.lock()
        if self.root is not None:
            self.root.goto("home", direction="right")

    def snack(self, text):
        MDSnackbar(MDLabel(text=text)).open()

    def on_keyboard(self, window, key, *args):
        if key == ANDROID_BACK_KEY and self.root is not None:
            return self.root.on_back()
        return False

    def on_pause(self):
        return True

    def on_resume(self):
        # L'application a été en arrière-plan, donc visible dans la liste des
        # tâches récentes : on redemande le mot de passe maître.
        self.lock()
