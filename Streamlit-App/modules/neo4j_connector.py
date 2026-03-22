"""Module de connexion à Neo4j/AuraDB."""
from neo4j import GraphDatabase


class Neo4jConnector:
    """Classe pour gérer la connexion à Neo4j/AuraDB."""

    def __init__(self, uri, user, password):
        """Initialise la connexion à Neo4j.

        Args:
            uri: URI de connexion Neo4j/AuraDB
            user: Nom d'utilisateur
            password: Mot de passe
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """Ferme la connexion au driver Neo4j."""
        self.driver.close()

    def get_all_labels(self):
        """Récupère tous les labels de nœuds disponibles.

        Returns:
            Liste des labels de nœuds
        """
        query = "CALL db.labels() YIELD label RETURN label"
        with self.driver.session() as session:
            result = session.run(query)
            return [record["label"] for record in result]

    def get_all_relation_types(self):
        """Récupère tous les types de relations disponibles.

        Returns:
            Liste des types de relations
        """
        query = (
            "CALL db.relationshipTypes() "
            "YIELD relationshipType RETURN relationshipType"
        )
        with self.driver.session() as session:
            result = session.run(query)
            return [record["relationshipType"] for record in result]

    def get_graph(self, labels=None, rel_types=None):
        """Récupère les nœuds et relations filtrés dynamiquement.

        Args:
            labels: Liste des labels de nœuds à filtrer (optionnel)
            rel_types: Liste des types de relations à filtrer (optionnel)

        Returns:
            Tuple (nodes, relationships) contenant les données du graphe
        """
        # Construire les filtres
        label_filter_n = ""
        label_filter_m = ""
        if labels:
            conditions = [f"'{cond}' IN labels(n)" for cond in labels]
            label_filter_n = "(" + " OR ".join(conditions) + ")"
            conditions_m = [f"'{cond}' IN labels(m)" for cond in labels]
            label_filter_m = "(" + " OR ".join(conditions_m) + ")"

        rel_filter = ""
        if rel_types:
            conditions = [f"type(r) = '{r_type}'" for r_type in rel_types]
            rel_filter = "(" + " OR ".join(conditions) + ")"

        # Construire la clause WHERE complète
        where_parts = []
        if label_filter_n:
            where_parts.append(label_filter_n)
        if label_filter_m:
            where_parts.append(label_filter_m)
        if rel_filter:
            where_parts.append(rel_filter)

        where_clause = ""
        if where_parts:
            where_clause = "WHERE " + " AND ".join(where_parts)

        query = f"""
        MATCH (n)-[r]->(m)
        {where_clause}
        RETURN DISTINCT n, r, m
        LIMIT 500
        """

        nodes = {}
        relationships = []

        with self.driver.session() as session:
            result = session.run(query)
            for record in result:
                n = record["n"]
                m = record["m"]
                r = record["r"]

                # Ajouter le nœud source
                if n and n.id not in nodes:
                    node_label = list(n.labels)[0] if n.labels else ""
                    nodes[n.id] = {
                        "id": n.id,
                        "label": node_label,
                        **dict(n.items())
                    }

                # Ajouter le nœud cible
                if m and m.id not in nodes:
                    node_label = list(m.labels)[0] if m.labels else ""
                    nodes[m.id] = {
                        "id": m.id,
                        "label": node_label,
                        **dict(m.items())
                    }

                # Ajouter la relation
                if r and n and m:
                    relationships.append({
                        "source": n.id,
                        "target": m.id,
                        "type": r.type
                    })

        return list(nodes.values()), relationships

    def get_all_movies(self):
        """Récupère tous les films (nœuds Movie) avec leurs titres.

        Returns:
            Liste de dictionnaires contenant id et title de chaque film
        """
        query = """
        MATCH (m:Movie)
        RETURN m.title as title, id(m) as id
        ORDER BY m.title
        """
        with self.driver.session() as session:
            result = session.run(query)
            return [
                {"id": record["id"], "title": record["title"]}
                for record in result
                if record["title"] is not None
            ]

    def get_movie_graph(self, movie_id, depth=2):
        """Récupère le graphe centré autour d'un film spécifique.

        Args:
            movie_id: ID du nœud film
            depth: Profondeur de la recherche (nombre de sauts)

        Returns:
            Tuple (nodes, relationships) pour le graphe autour du film
        """
        query = f"""
        MATCH path = (m:Movie)-[*1..{depth}]-(connected)
        WHERE id(m) = $movie_id
        UNWIND nodes(path) as node
        WITH collect(DISTINCT node) as allNodes
        UNWIND allNodes as n
        RETURN DISTINCT n, id(n) as node_id
        """

        nodes = {}
        relationships = []

        with self.driver.session() as session:
            # Récupérer les nœuds
            result = session.run(query, movie_id=movie_id)
            for record in result:
                n = record["n"]
                if n:
                    node_label = list(n.labels)[0] if n.labels else ""
                    nodes[n.id] = {
                        "id": n.id,
                        "label": node_label,
                        **dict(n.items())
                    }

            # Récupérer les relations entre ces nœuds uniquement
            node_ids = list(nodes.keys())
            if len(node_ids) > 0:
                rel_query = """
                MATCH (n)-[r]->(m)
                WHERE id(n) IN $node_ids AND id(m) IN $node_ids
                RETURN DISTINCT id(n) as source,
                id(m) as target, type(r) as type
                """
                result = session.run(rel_query, node_ids=node_ids)
                for record in result:
                    source_id = record["source"]
                    target_id = record["target"]
                    # Vérifier que les deux nœuds existent
                    if source_id in nodes and target_id in nodes:
                        relationships.append({
                            "source": source_id,
                            "target": target_id,
                            "type": record["type"]
                        })

        return list(nodes.values()), relationships
