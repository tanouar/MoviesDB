"""Tests unitaires pour modules/neo4j_connector.py (avec mocks).

Tous les tests utilisent unittest.mock pour simuler le driver Neo4j —
aucune connexion réelle à AuraDB ou à une instance locale n'est requise.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Ajout du dossier Streamlit-App au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent / "Streamlit-App"))

from modules.neo4j_connector import Neo4jConnector  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers pour construire des faux enregistrements Neo4j
# ---------------------------------------------------------------------------

def _make_node(element_id, labels, props):
    """Crée un faux nœud Neo4j."""
    node = MagicMock()
    node.element_id = element_id
    node.labels = labels
    node.items.return_value = list(props.items())
    # Permettre **dict(node.items()) dans le connector
    return node


def _make_record(**kwargs):
    """Crée un faux Record Neo4j avec accès par clé."""
    record = MagicMock()
    record.__getitem__ = lambda self, key: kwargs[key]
    return record


# ---------------------------------------------------------------------------
# Fixture : connecteur avec driver Neo4j mocké
# ---------------------------------------------------------------------------

@pytest.fixture
def connector():
    """Retourne un Neo4jConnector avec le driver GraphDatabase mocké."""
    with patch(
        "modules.neo4j_connector.GraphDatabase.driver"
    ) as mock_driver_cls:
        mock_driver = MagicMock()
        mock_driver_cls.return_value = mock_driver
        conn = Neo4jConnector(
            "bolt://localhost:7687", "neo4j", "password"
        )
        conn._mock_driver = mock_driver
        yield conn


# ---------------------------------------------------------------------------
# __init__ et close
# ---------------------------------------------------------------------------

class TestInit:
    def test_driver_instantiated(self):
        with patch(
            "modules.neo4j_connector.GraphDatabase.driver"
        ) as mock_driver_cls:
            Neo4jConnector("bolt://localhost:7687", "neo4j", "password")
            mock_driver_cls.assert_called_once_with(
                "bolt://localhost:7687", auth=("neo4j", "password")
            )

    def test_close_calls_driver_close(self, connector):
        connector.close()
        connector._mock_driver.close.assert_called_once()


# ---------------------------------------------------------------------------
# get_all_labels
# ---------------------------------------------------------------------------

class TestGetAllLabels:
    def test_returns_list_of_labels(self, connector):
        mock_session = MagicMock()
        mock_result = [
            _make_record(label="Movie"),
            _make_record(label="Person"),
        ]
        mock_session.run.return_value = iter(mock_result)
        connector._mock_driver.session.return_value.__enter__ = (
            lambda s: mock_session
        )
        connector._mock_driver.session.return_value.__exit__ = (
            MagicMock(return_value=False)
        )

        labels = connector.get_all_labels()

        assert labels == ["Movie", "Person"]

    def test_query_calls_db_labels(self, connector):
        mock_session = MagicMock()
        mock_session.run.return_value = iter([])
        connector._mock_driver.session.return_value.__enter__ = (
            lambda s: mock_session
        )
        connector._mock_driver.session.return_value.__exit__ = (
            MagicMock(return_value=False)
        )

        connector.get_all_labels()

        call_args = mock_session.run.call_args[0][0]
        assert "db.labels()" in call_args

    def test_empty_database_returns_empty_list(self, connector):
        mock_session = MagicMock()
        mock_session.run.return_value = iter([])
        connector._mock_driver.session.return_value.__enter__ = (
            lambda s: mock_session
        )
        connector._mock_driver.session.return_value.__exit__ = (
            MagicMock(return_value=False)
        )

        labels = connector.get_all_labels()

        assert labels == []


# ---------------------------------------------------------------------------
# get_all_relation_types
# ---------------------------------------------------------------------------

class TestGetAllRelationTypes:
    def test_returns_list_of_rel_types(self, connector):
        mock_session = MagicMock()
        mock_result = [
            _make_record(relationshipType="ACTED_IN"),
            _make_record(relationshipType="DIRECTED"),
        ]
        mock_session.run.return_value = iter(mock_result)
        connector._mock_driver.session.return_value.__enter__ = (
            lambda s: mock_session
        )
        connector._mock_driver.session.return_value.__exit__ = (
            MagicMock(return_value=False)
        )

        rel_types = connector.get_all_relation_types()

        assert rel_types == ["ACTED_IN", "DIRECTED"]

    def test_query_calls_db_relationship_types(self, connector):
        mock_session = MagicMock()
        mock_session.run.return_value = iter([])
        connector._mock_driver.session.return_value.__enter__ = (
            lambda s: mock_session
        )
        connector._mock_driver.session.return_value.__exit__ = (
            MagicMock(return_value=False)
        )

        connector.get_all_relation_types()

        call_args = mock_session.run.call_args[0][0]
        assert "relationshipTypes()" in call_args


# ---------------------------------------------------------------------------
# get_all_movies
# ---------------------------------------------------------------------------

class TestGetAllMovies:
    def test_returns_list_with_id_and_title(self, connector):
        mock_session = MagicMock()
        mock_result = [
            _make_record(id="id-1", title="Avengers"),
            _make_record(id="id-2", title="Iron Man"),
        ]
        mock_session.run.return_value = iter(mock_result)
        connector._mock_driver.session.return_value.__enter__ = (
            lambda s: mock_session
        )
        connector._mock_driver.session.return_value.__exit__ = (
            MagicMock(return_value=False)
        )

        movies = connector.get_all_movies()

        assert len(movies) == 2
        assert movies[0] == {"id": "id-1", "title": "Avengers"}
        assert movies[1] == {"id": "id-2", "title": "Iron Man"}

    def test_filters_none_titles(self, connector):
        mock_session = MagicMock()
        mock_result = [
            _make_record(id="id-1", title="Avengers"),
            _make_record(id="id-2", title=None),
        ]
        mock_session.run.return_value = iter(mock_result)
        connector._mock_driver.session.return_value.__enter__ = (
            lambda s: mock_session
        )
        connector._mock_driver.session.return_value.__exit__ = (
            MagicMock(return_value=False)
        )

        movies = connector.get_all_movies()

        assert len(movies) == 1
        assert movies[0]["title"] == "Avengers"
