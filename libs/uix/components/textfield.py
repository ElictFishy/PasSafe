"""Champ de saisie commun à toute l'application.

Enregistré dans la Factory par factory_registers.json : les fichiers kv
peuvent donc écrire `TextFieldRound:` sans importer quoi que ce soit.
"""

import os

from kivy.lang import Builder
from kivymd.uix.textfield import MDTextField

from config import kv_path

Builder.load_file(kv_path(os.path.join("components", "textfield.kv")))


class TextFieldRound(MDTextField):
    pass
