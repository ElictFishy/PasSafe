"""Écran racine : il contient le gestionnaire d'écrans et la navigation."""

import importlib
import json
import os

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from config import ROOT_DIR, kv_path

Builder.load_file(kv_path("root.kv"))


class Root(MDScreen):
    manager = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with open(
            os.path.join(ROOT_DIR, "screens.json"), encoding="utf-8"
        ) as fd:
            self.screens_data = json.load(fd)

    def goto(self, screen_name, direction="left"):
        screen = self.load_screen(screen_name)
        self.manager.transition.direction = direction
        self.manager.current = screen_name
        return screen

    def load_screen(self, screen_name):
        """Instancie l'écran au premier affichage seulement.

        Charger les trois écrans au démarrage rallongerait le temps
        d'ouverture pour des vues que l'utilisateur n'atteindra peut-être pas.
        """
        if self.manager.has_screen(screen_name):
            return self.manager.get_screen(screen_name)

        try:
            data = self.screens_data[screen_name]
        except KeyError:
            raise ValueError(
                "Écran absent de screens.json : %s" % screen_name
            ) from None

        module = importlib.import_module(data["module"])
        screen = getattr(module, data["class"])(name=screen_name)
        self.manager.add_widget(screen)
        return screen

    def on_back(self):
        """Touche retour d'Android. True : l'application garde la main."""
        current = self.manager.current
        if current == "entry":
            self.goto("pass", direction="right")
            return True
        if current == "pass":
            MDApp.get_running_app().lock()
            return True
        return False
