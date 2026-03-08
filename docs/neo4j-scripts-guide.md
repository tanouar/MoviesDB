# Scripts Neo4j - Guide d'utilisation

## Scripts disponibles

### 1. `load_into_neo4j.py` - Chargement local (Docker)
Charge les données dans une instance Neo4j locale (Docker).

```bash
python pipeline/load_into_neo4j.py
```

**Configuration** :
- URI: `bolt://0.0.0.0:7687`
- Username: `neo4j`
- Password: `plbconsultant`

### 2. `load_into_auradb.py` - Chargement AuraDB
Charge les données dans Neo4j AuraDB (cloud).

```bash
python pipeline/load_into_auradb.py
```

**Configuration** (via `.env`) :
```env
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=votre-mot-de-passe
NEO4J_DATABASE=neo4j
AURA_INSTANCEID=xxxxxxxx
AURA_INSTANCENAME=MonInstance
```

### 3. `clean_neo4j.py` - Nettoyage de la base

Supprime toutes les contraintes, index et données.

#### Usage Local (Docker)

```bash
python pipeline/clean_neo4j.py
```

#### Usage AuraDB

```bash
python pipeline/clean_neo4j.py --auradb
```

#### Options avancées

```bash
# Connexion personnalisée
python pipeline/clean_neo4j.py \
  --uri bolt://localhost:7687 \
  --username neo4j \
  --password monpassword \
  --database neo4j
```

## Résolution de l'erreur de contrainte

### Problème

```
Neo.ClientError.Schema.ConstraintValidationFailed
Node with label `Character` must have the property `person_id`
```

### Cause

Une contrainte existe dans la base qui exige que les nœuds `Character` aient une propriété `person_id`, ce qui ne correspond pas à notre modèle de données.

### Solutions

#### Solution 1 : Utiliser les scripts mis à jour (recommandé)

Les scripts `load_into_neo4j.py` et `load_into_auradb.py` ont été mis à jour pour :
- ✅ Supprimer automatiquement toutes les contraintes avant le chargement
- ✅ Supprimer automatiquement tous les index avant le chargement
- ✅ Recréer les index appropriés à la fin

Relancez simplement :
```bash
python pipeline/load_into_auradb.py
# ou
python pipeline/load_into_neo4j.py
```

#### Solution 2 : Nettoyer manuellement

Si vous voulez nettoyer la base avant de recharger :

```bash
# Pour local
python pipeline/clean_neo4j.py

# Pour AuraDB
python pipeline/clean_neo4j.py --auradb
```

Puis relancez le chargement.

#### Solution 3 : Via Cypher (si vous préférez)

Connectez-vous à Neo4j Browser et exécutez :

```cypher
// Lister toutes les contraintes
SHOW CONSTRAINTS;

// Supprimer une contrainte spécifique (remplacez le nom)
DROP CONSTRAINT constraint_name;

// Supprimer tous les index
SHOW INDEXES;
DROP INDEX index_name;

// Supprimer toutes les données
MATCH (n) DETACH DELETE n;
```

## Modèle de données

Notre modèle de données Marvel :

### Nœuds

- **Character** : `{name: string}`
- **Person** : `{id: string, name: string, birth_year: int, death_year: int}`
- **Movie** : `{id: string, title: string, year: int, runtime: int, genres: [string]}`

### Relations

- `(Person)-[:PLAY]->(Character)` - Un acteur joue un personnage
- `(Character)-[:APPEAR_IN]->(Movie)` - Un personnage apparaît dans un film
- `(Person)-[:DIRECTED]->(Movie)` - Un réalisateur dirige un film
- `(Person)-[:PRODUCED]->(Movie)` - Un producteur produit un film

### Labels secondaires

- `Person` peut aussi avoir le label `Actor` s'il joue un personnage

## Index créés automatiquement

Les scripts créent automatiquement ces index pour améliorer les performances :

```cypher
CREATE INDEX character_name_index IF NOT EXISTS FOR (c:Character) ON (c.name)
CREATE INDEX person_id_index IF NOT EXISTS FOR (p:Person) ON (p.id)
CREATE INDEX movie_id_index IF NOT EXISTS FOR (m:Movie) ON (m.id)
CREATE INDEX movie_title_index IF NOT EXISTS FOR (m:Movie) ON (m.title)
```

## Vérification post-chargement

Après le chargement, vérifiez les données :

```cypher
// Compter les nœuds par type
MATCH (n) RETURN labels(n) as Type, count(n) as Count

// Vérifier les contraintes
SHOW CONSTRAINTS

// Vérifier les index
SHOW INDEXES

// Exemple de données
MATCH (p:Person)-[:PLAY]->(c:Character)-[:APPEAR_IN]->(m:Movie)
RETURN p.name, c.name, m.title
LIMIT 10
```
