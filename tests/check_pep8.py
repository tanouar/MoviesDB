#!/usr/bin/env python3
"""
Script de vérification PEP8 pour tous les fichiers Python du repository.
Utilise pycodestyle pour vérifier la conformité au standard PEP8.

Usage:
    python tests/check_pep8.py
"""

import sys
import os
from pathlib import Path
try:
    import pycodestyle
except ImportError:
    print("❌ pycodestyle n'est pas installé.")
    print("   Installez-le avec: pip install -r requirements-lint.txt")
    sys.exit(1)


def find_python_files(root_dir="."):
    """
    Trouve tous les fichiers Python dans le repository.

    Exclut automatiquement:
    - Les environnements virtuels (venv, .venv, env, .env)
    - Les dossiers de build et distribution
    - Les répertoires Git et cache
    - Le dossier docker
    - Les checkpoints Jupyter

    Args:
        root_dir (str): Répertoire racine à scanner

    Returns:
        list: Liste triée des chemins de fichiers Python
    """
    excluded_dirs = {
        'venv', '.venv', 'env', '.env',
        'node_modules', '.git', '__pycache__',
        '.pytest_cache', '.tox', 'dist', 'build',
        '.eggs', '*.egg-info', 'docker',
        '.ipynb_checkpoints'
    }

    python_files = []
    root_path = Path(root_dir)

    print(f"🔎 Recherche des fichiers Python dans: {root_path.absolute()}\n")

    for py_file in root_path.rglob("*.py"):
        # Vérifie si le fichier est dans un répertoire exclu
        if not any(excluded in py_file.parts for excluded in excluded_dirs):
            python_files.append(str(py_file))
            print(f"   ✓ Trouvé: {py_file}")

    return sorted(python_files)


def check_pep8_compliance(files, config_file=None):
    """
    Vérifie la conformité PEP8 des fichiers donnés.

    Args:
        files (list): Liste des fichiers à vérifier
        config_file (str, optional): Fichier de configuration

    Returns:
        tuple: (nombre_total_erreurs, résultat_style_guide)
    """
    # Configuration par défaut
    style_config = {
        'quiet': False,
        'show_source': True,
        'show_pep8': True,
    }

    # Charge la configuration depuis .pycodestyle ou setup.cfg
    if config_file and os.path.exists(config_file):
        style = pycodestyle.StyleGuide(
            config_file=config_file, **style_config)
    else:
        # Cherche automatiquement .pycodestyle à la racine
        style = pycodestyle.StyleGuide(**style_config)

    print("\n" + "="*70)
    print("🔍 VÉRIFICATION PEP8 EN COURS")
    print("="*70)
    print(f"📁 Nombre de fichiers à vérifier: {len(files)}\n")

    result = style.check_files(files)

    return result.total_errors, result


def print_summary(total_errors, file_count):
    """
    Affiche un résumé coloré des résultats.

    Args:
        total_errors (int): Nombre total d'erreurs détectées
        file_count (int): Nombre de fichiers vérifiés

    Returns:
        bool: True si conforme (0 erreur), False sinon
    """
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DE LA VÉRIFICATION PEP8")
    print("="*70)
    print(f"📂 Fichiers vérifiés: {file_count}")
    print(f"🐛 Erreurs totales: {total_errors}")

    if total_errors == 0:
        print("\n✅ SUCCÈS: Tous les fichiers sont conformes à PEP8 !")
        print("="*70)
        return True
    else:
        print(f"\n❌ ÉCHEC: {total_errors} violation(s) PEP8 détectée(s)")
        print("\n💡 Conseil: Utilisez 'autopep8' pour corriger "
              "automatiquement:")
        print("   autopep8 --in-place --aggressive --aggressive <fichier>")
        print("="*70)
        return False


def main():
    """
    Fonction principale du script.

    - Change le répertoire vers la racine du projet
    - Trouve tous les fichiers Python
    - Vérifie leur conformité PEP8
    - Affiche un résumé
    - Retourne un code de sortie approprié pour CI/CD
    """
    # Change le répertoire de travail vers la racine du projet
    # Le script est dans tests/, on remonte d'un niveau
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    os.chdir(root_dir)

    print("="*70)
    print("🎬 MoviesDB - Vérification PEP8")
    print("="*70)
    print(f"📂 Répertoire racine du projet: {root_dir.absolute()}\n")

    # Cherche les fichiers Python depuis la racine
    python_files = find_python_files(".")

    if not python_files:
        print("\n⚠️  Aucun fichier Python trouvé dans le repository")
        print("   Vérifiez que vous êtes dans le bon répertoire.")
        sys.exit(0)

    # Vérifie la conformité PEP8
    total_errors, _ = check_pep8_compliance(python_files)

    # Affiche le résumé
    is_compliant = print_summary(total_errors, len(python_files))

    # Exit code: 0 si conforme, 1 sinon (important pour CI/CD)
    sys.exit(0 if is_compliant else 1)


if __name__ == "__main__":
    main()
