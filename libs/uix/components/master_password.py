"""Contenu de la boîte de dialogue « changer le mot de passe maître »."""

import os

from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.uix.boxlayout import MDBoxLayout

from config import kv_path

Builder.load_file(kv_path(os.path.join("components", "master_password.kv")))


class MasterPasswordContent(MDBoxLayout):
    error = StringProperty("")
