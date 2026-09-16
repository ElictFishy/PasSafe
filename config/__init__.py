"""Chemins du projet, résolus une fois pour toutes.

Sur Android, le répertoire courant n'est pas forcément celui de
l'application : les fichiers kv et json sont donc toujours ouverts par chemin
absolu, calculé à partir de ce module.
"""

import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KV_DIR = os.path.join(ROOT_DIR, "libs", "uix", "kv")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")


def kv_path(name):
    return os.path.join(KV_DIR, name)
