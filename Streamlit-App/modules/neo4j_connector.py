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
        # Requête simple sans WHERE complexe — filtrage côté Python
        query = """
        MATCH (n)-[r]->(m)
        RETURN DISTINCT n, r, m
        LIMIT 1000
        """

        nodes = {}
        relationships = []

        with self.driver.session() as session:
            result = session.run(query)
            for record in result:
                n = record["n"]
                m = record["m"]
                r = record["r"]

                n_eid = n.element_id if n else None
                m_eid = m.element_id if m else None

                if n and n_eid not in nodes:
                    node_label = list(n.labels)[0] if n.labels else ""
                    nodes[n_eid] = {
                        **dict(n.items()),
                        "id": n_eid,
                        "label": node_label
                    }
                if m and m_eid not in nodes:
                    node_label = list(m.labels)[0] if m.labels else ""
                    nodes[m_eid] = {
                        **dict(m.items()),
                        "id": m_eid,
                        "label": node_label
                    }
                if r is not None and n_eid and m_eid:
                    relationships.append({
                        "source": n_eid,
                        "target": m_eid,
                        "type": r.type
                    })

        # Filtrage côté Python par labels
        if labels:
            label_set = set(labels)
            filtered_nodes = {
                k: v for k, v in nodes.items()
                if v.get("label") in label_set
            }
        else:
            filtered_nodes = nodes

        # Filtrage des relations (les deux nœuds doivent être présents)
        filtered_rels = [
            rel for rel in relationships
            if rel["source"] in filtered_nodes
            and rel["target"] in filtered_nodes
        ]

        # Filtrage par types de relations
        if rel_types:
            rel_type_set = set(rel_types)
            filtered_rels = [
                rel for rel in filtered_rels
                if rel["type"] in rel_type_set
            ]

        return list(filtered_nodes.values()), filtered_rels

    def get_all_movies(self):
        """Récupère tous les films (nœuds Movie) avec leurs titres.

        Returns:
            Liste de dictionnaires contenant id et title de chaque film
        """
        query = """
        MATCH (m:Movie)
        RETURN m.title as title, elementId(m) as id
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
        WHERE elementId(m) = $movie_id
        UNWIND nodes(path) as node
        WITH collect(DISTINCT node) as allNodes
        UNWIND allNodes as n
        RETURN DISTINCT n
        """

        nodes = {}
        relationships = []

        with self.driver.session() as session:
            # Récupérer les nœuds
            result = session.run(query, movie_id=movie_id)
            for record in result:
                n = record["n"]
                if n:
                    n_eid = n.element_id
                    node_label = list(n.labels)[0] if n.labels else ""
                    nodes[n_eid] = {
                        **dict(n.items()),
                        "id": n_eid,
                        "label": node_label
                    }

            # Récupérer les relations entre ces nœuds uniquement
            node_ids = list(nodes.keys())
            if len(node_ids) > 0:
                rel_query = """
                MATCH (n)-[r]->(m)
                WHERE elementId(n) IN $node_ids
                  AND elementId(m) IN $node_ids
                RETURN DISTINCT elementId(n) as source,
                elementId(m) as target, type(r) as type
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
