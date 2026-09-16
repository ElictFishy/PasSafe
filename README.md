# PasSafe

Gestionnaire de mots de passe pour Android, écrit en Python avec Kivy et
KivyMD. Le coffre est un fichier chiffré en AES-256-GCM, ouvert par un mot de
passe maître. Rien ne sort du téléphone : pas de compte, pas de serveur, et
l'application ne demande aucune permission.

## Fonctions

- Création du coffre et déverrouillage par mot de passe maître
- Ajout, modification et suppression d'entrées (service, identifiant, mot de
  passe, adresse, notes)
- Recherche dans les entrées, le mot de passe exclu de la recherche
- Générateur paramétrable : longueur, majuscules, chiffres, caractères
  spéciaux, caractères ambigus écartés
- Copie dans le presse-papier, effacé automatiquement au bout de 30 secondes
- Changement du mot de passe maître, avec re-chiffrement du coffre
- Verrouillage manuel, et automatique dès que l'application passe en
  arrière-plan

## Chiffrement

| | |
|---|---|
| Dérivation de clé | PBKDF2-HMAC-SHA256, 200 000 itérations, sel de 16 octets |
| Chiffrement | AES-256-GCM (nonce et tag enregistrés à côté du chiffré) |
| Emplacement | `user_data_dir/passafe.vault`, dossier privé de l'application |

Le fichier ne contient que le sel, le nombre d'itérations et le bloc chiffré :
les titres, identifiants et mots de passe n'existent en clair qu'en mémoire,
pendant que le coffre est déverrouillé. Le mot de passe maître n'est jamais
enregistré, et GCM détecte au passage un fichier modifié.

Ce qui reste hors de portée de l'application : un mot de passe maître trop
court (huit caractères minimum sont imposés, ce n'est pas beaucoup), et un
téléphone déjà compromis.

## Structure

```
main.py                     Point d'entrée : enregistre les widgets, lance l'app
passafe.py                  Classe application : thème, coffre, verrouillage
screens.json                Écrans, chargés à la demande
factory_registers.json      Widgets maison utilisables depuis les fichiers kv

utils/crypto.py             AES-256-GCM et dérivation PBKDF2
utils/vault.py              Entrées, lecture et écriture du coffre
utils/generator.py          Génération et solidité des mots de passe
utils/clipboard.py          Copie et effacement du presse-papier

libs/uix/baseclass/         Logique des écrans (root, home, pass, entry)
libs/uix/components/        Widgets réutilisables (champ, générateur, mot de passe maître)
libs/uix/kv/                Vues correspondantes
config/                     Chemins du projet et styles de texte

tests/                      Tests du coffre et du générateur, sans interface
```

## Lancer sur le bureau

```bash
pip install kivy==2.3.1 kivymd==1.2.0 pycryptodome pillow
python main.py
```

Le coffre est alors créé dans le dossier de données utilisateur de Kivy, pas
dans le dépôt.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Compiler l'APK

La compilation passe par Buildozer, configuré dans `buildozer.spec`, et le
workflow GitHub Actions la lance à chaque push sur `main` : l'APK est déposé
dans les artéfacts de l'exécution. En local, sous Linux :

```bash
buildozer -v android debug
```
