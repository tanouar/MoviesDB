# GitHub Actions Workflows

## 🔍 PEP8 Compliance Check

Ce workflow vérifie automatiquement que tous les fichiers Python du repository respectent le standard PEP8.

### Déclenchement

Le workflow se déclenche :
- ✅ À chaque push sur les branches `main`, `master`, `develop`, `features` (si des fichiers `.py` sont modifiés)
- ✅ À chaque pull request vers `main`, `master`, `develop`
- ✅ Manuellement via l'onglet "Actions" → "Run workflow"

### Fonctionnement

1. **Checkout du code** : Récupère le code source
2. **Configuration Python** : Installe Python 3.11
3. **Installation des dépendances** : Installe pycodestyle, flake8, autopep8
4. **Vérification PEP8** : Execute `tests/check_pep8.py`
5. **Rapport détaillé** : Si échec, génère un rapport flake8 détaillé

### Configuration

Les règles PEP8 sont configurées dans :
- `.pycodestyle` : Configuration principale
- `.flake8` : Configuration avancée (linting)

### Résolution des erreurs

Si le workflow échoue :

```bash
# Vérifier localement
python tests/check_pep8.py

# Auto-corriger les erreurs
autopep8 --in-place --aggressive --aggressive <fichier>

# Ou corriger tout le projet
autopep8 --in-place --aggressive --aggressive --recursive .
```