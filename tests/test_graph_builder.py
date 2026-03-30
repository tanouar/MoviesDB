"""Tests unitaires pour modules/graph_builder.py."""
import sys
from pathlib import Path

import pytest

# Ajout du dossier Streamlit-App au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent / "Streamlit-App"))

from modules.graph_builder import (  # noqa: E402
    apply_caption_template,
    build_pyvis_graph,
    clean_value,
    color_from_label,
    hex_to_rgba,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

NODES_SIMPLE = [
    {"id": "a", "label": "Movie", "title": "Avengers"},
    {"id": "b", "label": "Person", "name": "Robert Downey Jr."},
    {"id": "c", "label": "Person", "name": "Chris Evans"},
]
RELS_SIMPLE = [
    {"source": "a", "target": "b", "type": "ACTED_IN"},
    {"source": "a", "target": "c", "type": "ACTED_IN"},
]


# ---------------------------------------------------------------------------
# hex_to_rgba
# ---------------------------------------------------------------------------

class TestHexToRgba:
    def test_valid_6_char(self):
        assert hex_to_rgba("#296218") == "#296218"

    def test_valid_8_char(self):
        result = hex_to_rgba("#296218FF")
        assert result.startswith("rgba(")

    def test_non_string_passthrough(self):
        assert hex_to_rgba(42) == 42

    def test_invalid_hex_passthrough(self):
        assert hex_to_rgba("not-a-color") == "not-a-color"

    def test_none_passthrough(self):
        assert hex_to_rgba(None) is None


# ---------------------------------------------------------------------------
# clean_value
# ---------------------------------------------------------------------------

class TestCleanValue:
    def test_strips_double_quotes(self):
        assert clean_value('"hello"') == "hello"

    def test_strips_single_quotes(self):
        assert clean_value("'hello'") == "hello"

    def test_strips_whitespace(self):
        assert clean_value("  hello  ") == "hello"

    def test_none_returns_none(self):
        assert clean_value(None) is None

    def test_plain_value_unchanged(self):
        assert clean_value("hello") == "hello"


# ---------------------------------------------------------------------------
# apply_caption_template
# ---------------------------------------------------------------------------

class TestApplyCaptionTemplate:
    def test_replaces_placeholder(self):
        result = apply_caption_template("{name}", {"name": "Iron Man"})
        assert result == "Iron Man"

    def test_multiple_placeholders(self):
        result = apply_caption_template(
            "{name} ({year})",
            {"name": "Avengers", "year": "2012"}
        )
        assert result == "Avengers (2012)"

    def test_missing_key_empty_string(self):
        result = apply_caption_template("{missing}", {"name": "test"})
        assert result == ""

    def test_none_template_returns_none(self):
        assert apply_caption_template(None, {"name": "test"}) is None

    def test_empty_template(self):
        assert apply_caption_template("", {"name": "test"}) is None


# ---------------------------------------------------------------------------
# color_from_label
# ---------------------------------------------------------------------------

class TestColorFromLabel:
    def test_returns_rgb_string(self):
        color = color_from_label("Movie")
        assert color.startswith("rgb(")

    def test_deterministic(self):
        assert color_from_label("Actor") == color_from_label("Actor")

    def test_different_labels_different_colors(self):
        assert color_from_label("Movie") != color_from_label("Person")


# ---------------------------------------------------------------------------
# build_pyvis_graph
# ---------------------------------------------------------------------------

class TestBuildPyvisGraph:
    def test_returns_html_string(self):
        html = build_pyvis_graph(NODES_SIMPLE, RELS_SIMPLE, debug=False)
        assert isinstance(html, str)
        assert len(html) > 0

    def test_html_contains_html_tag(self):
        html = build_pyvis_graph(NODES_SIMPLE, RELS_SIMPLE, debug=False)
        assert "<html" in html.lower()

    def test_empty_graph_does_not_raise(self):
        html = build_pyvis_graph([], [], debug=False)
        assert isinstance(html, str)

    def test_with_bc_scores(self):
        bc_scores = {"a": 0.8, "b": 0.1, "c": 0.0}
        html = build_pyvis_graph(
            NODES_SIMPLE, RELS_SIMPLE,
            debug=False,
            bc_scores=bc_scores,
            bc_threshold=0.5,
        )
        assert isinstance(html, str)
        # Le nœud "a" est un pont (BC > seuil) → couleur #296218 présente
        assert "#296218" in html

    def test_with_communities(self):
        communities = {"a": 0, "b": 1, "c": 1}
        html = build_pyvis_graph(
            NODES_SIMPLE, RELS_SIMPLE,
            debug=False,
            communities=communities,
        )
        assert isinstance(html, str)

    def test_bc_below_threshold_no_bridge_color(self):
        """Nœud avec BC sous le seuil ne doit pas avoir la couleur pont."""
        bc_scores = {"a": 0.05, "b": 0.02, "c": 0.01}
        html = build_pyvis_graph(
            NODES_SIMPLE, RELS_SIMPLE,
            debug=False,
            bc_scores=bc_scores,
            bc_threshold=0.5,
        )
        # Aucun nœud ne dépasse le seuil → pas de couleur pont
        assert "#296218" not in html

    def test_custom_height(self):
        html = build_pyvis_graph(
            NODES_SIMPLE, RELS_SIMPLE,
            height="900px",
            debug=False
        )
        assert "900px" in html
