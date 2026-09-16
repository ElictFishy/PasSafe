import os
import sys

root_dir = os.path.split(os.path.abspath(sys.argv[0]))[0]
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, "libs", "uix"))

import json  # NOQA: E402

from kivy.factory import Factory  # NOQA: E402

from passafe import PasSafe  # NOQA: E402

__version__ = "1.0"


r = Factory.register

# Les widgets maison sont enregistrés avant le chargement des fichiers kv,
# qui peuvent alors les utiliser sans import.
with open(os.path.join(root_dir, "factory_registers.json")) as fd:
    custom_widgets = json.load(fd)
    for module, _classes in custom_widgets.items():
        for _class in _classes:
            r(_class, module=module)

PasSafe().run()
