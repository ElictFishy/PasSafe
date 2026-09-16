"""Génération de mots de passe et estimation de leur solidité."""

import math
import secrets
import string

LOWERCASE = string.ascii_lowercase
UPPERCASE = string.ascii_uppercase
DIGITS = string.digits
SYMBOLS = "!#$%&*+-=?@^_~"

# Caractères que l'on confond en les recopiant à la main.
AMBIGUOUS = "Il1O0"

MIN_LENGTH = 8
MAX_LENGTH = 64
DEFAULT_LENGTH = 20

STRENGTH_LABELS = [
    "Très faible",
    "Faible",
    "Correct",
    "Bon",
    "Excellent",
]


def generate(
    length=DEFAULT_LENGTH,
    uppercase=True,
    digits=True,
    symbols=True,
    avoid_ambiguous=True,
):
    """Tire un mot de passe, au moins un caractère par famille choisie."""
    length = max(MIN_LENGTH, min(MAX_LENGTH, int(length)))

    families = [LOWERCASE]
    if uppercase:
        families.append(UPPERCASE)
    if digits:
        families.append(DIGITS)
    if symbols:
        families.append(SYMBOLS)

    if avoid_ambiguous:
        families = [
            "".join(c for c in family if c not in AMBIGUOUS)
            for family in families
        ]

    alphabet = "".join(families)
    # Un caractère imposé par famille, le reste tiré dans tout l'alphabet : le
    # mot de passe satisfait ainsi les sites qui exigent chaque type.
    chars = [secrets.choice(family) for family in families]
    chars += [secrets.choice(alphabet) for _ in range(length - len(chars))]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def entropy_bits(password):
    """Entropie approchée, déduite des familles de caractères présentes."""
    if not password:
        return 0.0

    known = LOWERCASE + UPPERCASE + DIGITS + SYMBOLS
    pool = 0
    for family in (LOWERCASE, UPPERCASE, DIGITS, SYMBOLS):
        if any(c in family for c in password):
            pool += len(family)
    if any(c not in known for c in password):
        pool += 32  # accents, espaces, ponctuation rare

    return len(password) * math.log2(pool) if pool else 0.0


def strength(password):
    """Renvoie (score de 0 à 4, libellé) pour la jauge de l'interface."""
    bits = entropy_bits(password)
    for index, limit in enumerate((28, 50, 70, 90)):
        if bits < limit:
            return index, STRENGTH_LABELS[index]
    return 4, STRENGTH_LABELS[4]
