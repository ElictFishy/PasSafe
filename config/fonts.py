"""Styles de texte propres à PasSafe, ajoutés à ceux de KivyMD.

Format attendu par `theme_cls.font_styles` : [police, taille, capitales,
interlettrage]. Les polices Roboto sont livrées avec KivyMD, il n'y a donc
aucun fichier de police à embarquer dans l'APK.
"""

font_styles = {
    "Logo": ["RobotoMedium", 34, False, 1.5],
    "Field": ["Roboto", 17, False, 0],
    "Secret": ["RobotoMedium", 18, False, 2],
    "Hint": ["Roboto", 13, False, 0.2],
}
