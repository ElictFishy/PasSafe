"""Copie dans le presse-papier, avec effacement automatique.

Copier un mot de passe vaut mieux que l'afficher, mais le presse-papier
d'Android est lisible par les autres applications : on l'efface donc au bout
de quelques secondes, et tout de suite au verrouillage du coffre.
"""

from kivy.clock import Clock
from kivy.core.clipboard import Clipboard

CLEAR_DELAY = 30  # secondes

_scheduled_clear = None
_copied_value = None


def copy(text, clear_after=CLEAR_DELAY):
    global _scheduled_clear, _copied_value

    Clipboard.copy(text)
    _copied_value = text
    if _scheduled_clear is not None:
        _scheduled_clear.cancel()
    _scheduled_clear = Clock.schedule_once(lambda dt: clear_now(), clear_after)


def clear_now():
    """Efface le presse-papier s'il contient encore un secret de PasSafe."""
    global _scheduled_clear, _copied_value

    if _scheduled_clear is not None:
        _scheduled_clear.cancel()
        _scheduled_clear = None
    if _copied_value is None:
        return

    try:
        # On n'efface que si notre valeur est toujours là, pour ne pas jeter
        # ce que l'utilisateur a copié entre-temps.
        still_ours = Clipboard.paste() == _copied_value
    except Exception:
        # Certains appareils refusent la lecture du presse-papier en arrière-
        # plan : dans le doute, on efface.
        still_ours = True

    if still_ours:
        Clipboard.copy("")
    _copied_value = None
