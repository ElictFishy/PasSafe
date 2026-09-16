"""Contenu du générateur, affiché dans une boîte de dialogue."""

import os

from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.uix.boxlayout import MDBoxLayout

from config import kv_path
from utils import generator

Builder.load_file(kv_path(os.path.join("components", "generator.kv")))


class GeneratorContent(MDBoxLayout):
    password = StringProperty("")

    def on_kv_post(self, base_widget):
        self.shuffle()

    def shuffle(self, *args):
        self.password = generator.generate(
            length=int(self.ids.length.value),
            uppercase=self.ids.uppercase.active,
            digits=self.ids.digits.active,
            symbols=self.ids.symbols.active,
        )
