"""Tests unitaires pour modules/graph_analyzer.py."""
import sys
from pathlib import Path

import pytest

# Ajout du dossier Streamlit-App au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent / "Streamlit-App"))

from modules.graph_analyzer import (  # noqa: E402
    COMMUNITY_METHODS,
    analyze_graph,
    build_nx_graph,
    compute_betweenness,
    detect_communities,
    get_community_color,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

NODES_LINE = [
    {"id": "a"},
    {"id": "b"},
    {"id": "c"},
    {"id": "d"},
]
RELS_LINE = [
    {"source": "a", "target": "b"},
    {"source": "b", "target": "c"},
    {"source": "c", "target": "d"},
]

NODES_STAR = [
    {"id": "hub"},
    {"id": "n1"},
    {"id": "n2"},
    {"id": "n3"},
]
RELS_STAR = [
    {"source": "hub", "target": "n1"},
    {"source": "hub", "target": "n2"},
    {"source": "hub", "target": "n3"},
]


# ---------------------------------------------------------------------------
# build_nx_graph
# ---------------------------------------------------------------------------

class TestBuildNxGraph:
    def test_nodes_added(self):
        G = build_nx_graph(NODES_LINE, RELS_LINE)
        assert set(G.nodes()) == {"a", "b", "c", "d"}

    def test_edges_added(self):
        G = build_nx_graph(NODES_LINE, RELS_LINE)
        assert G.number_of_edges() == 3

    def test_empty_nodes(self):
        G = build_nx_graph([], [])
        assert G.number_of_nodes() == 0
        assert G.number_of_edges() == 0

    def test_unknown_source_ignored(self):
        rels = [{"source": "UNKNOWN", "target": "a"}]
        G = build_nx_graph(NODES_LINE, rels)
        assert G.number_of_edges() == 0

    def test_unknown_target_ignored(self):
        rels = [{"source": "a", "target": "UNKNOWN"}]
        G = build_nx_graph(NODES_LINE, rels)
        assert G.number_of_edges() == 0


# ---------------------------------------------------------------------------
# compute_betweenness
# ---------------------------------------------------------------------------

class TestComputeBetweenness:
    def test_returns_all_nodes(self):
        G = build_nx_graph(NODES_LINE, RELS_LINE)
        bc = compute_betweenness(G)
        assert set(bc.keys()) == {"a", "b", "c", "d"}

    def test_scores_between_0_and_1(self):
        G = build_nx_graph(NODES_LINE, RELS_LINE)
        bc = compute_betweenness(G, normalized=True)
        for score in bc.values():
            assert 0.0 <= score <= 1.0

    def test_hub_has_highest_bc(self):
        """Le nœud hub d'un graphe étoile doit avoir le BC le plus élevé."""
        G = build_nx_graph(NODES_STAR, RELS_STAR)
        bc = compute_betweenness(G)
        assert bc["hub"] == max(bc.values())

    def test_empty_graph(self):
        G = build_nx_graph([], [])
        bc = compute_betweenness(G)
        assert bc == {}


# ---------------------------------------------------------------------------
# detect_communities
# ---------------------------------------------------------------------------

class TestDetectCommunities:
    def test_components_single_chain(self):
        """Une chaîne linéaire = 1 composante connexe."""
        G = build_nx_graph(NODES_LINE, RELS_LINE)
        communities = detect_communities(G, method="components")
        assert len(set(communities.values())) == 1

    def test_components_two_disconnected(self):
        """Deux groupes déconnectés = 2 composantes."""
        nodes = [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "d"}]
        rels = [
            {"source": "a", "target": "b"},
            {"source": "c", "target": "d"},
        ]
        G = build_nx_graph(nodes, rels)
        communities = detect_communities(G, method="components")
        assert len(set(communities.values())) == 2

    def test_all_nodes_assigned(self):
        G = build_nx_graph(NODES_LINE, RELS_LINE)
        communities = detect_communities(G, method="components")
        assert set(communities.keys()) == {"a", "b", "c", "d"}

    def test_unknown_method_fallback_to_components(self):
        """Une méthode inconnue doit tomber sur composantes connexes."""
        G = build_nx_graph(NODES_LINE, RELS_LINE)
        communities = detect_communities(G, method="invalid_method")
        assert len(communities) == 4


# ---------------------------------------------------------------------------
# analyze_graph
# ---------------------------------------------------------------------------

class TestAnalyzeGraph:
    def test_returns_expected_keys(self):
        result = analyze_graph(NODES_LINE, RELS_LINE)
        assert "bc" in result
        assert "communities" in result
        assert "top_bridges" in result

    def test_bc_covers_all_nodes(self):
        result = analyze_graph(NODES_LINE, RELS_LINE)
        assert set(result["bc"].keys()) == {"a", "b", "c", "d"}

    def test_top_bridges_sorted_descending(self):
        result = analyze_graph(NODES_STAR, RELS_STAR)
        scores = [score for _, score in result["top_bridges"]]
        assert scores == sorted(scores, reverse=True)

    def test_hub_is_first_bridge(self):
        result = analyze_graph(NODES_STAR, RELS_STAR)
        top_node, _ = result["top_bridges"][0]
        assert top_node == "hub"

    def test_empty_nodes_does_not_raise(self):
        result = analyze_graph([], [])
        assert result["bc"] == {}
        assert result["communities"] == {}
        assert result["top_bridges"] == []

    def test_community_method_components(self):
        result = analyze_graph(
            NODES_LINE, RELS_LINE, community_method="components"
        )
        assert isinstance(result["communities"], dict)

    def test_nodes_without_relations(self):
        nodes = [{"id": "x"}, {"id": "y"}]
        result = analyze_graph(nodes, [])
        assert len(result["bc"]) == 2
        for score in result["bc"].values():
            assert score == 0.0


# ---------------------------------------------------------------------------
# COMMUNITY_METHODS
# ---------------------------------------------------------------------------

class TestCommunityMethods:
    def test_all_keys_present(self):
        assert "Louvain" in COMMUNITY_METHODS
        assert "Leiden" in COMMUNITY_METHODS
        assert "Composantes connexes" in COMMUNITY_METHODS

    def test_values_are_strings(self):
        for v in COMMUNITY_METHODS.values():
            assert isinstance(v, str)


# ---------------------------------------------------------------------------
# get_community_color
# ---------------------------------------------------------------------------

class TestGetCommunityColor:
    def test_returns_hex_string(self):
        color = get_community_color(0)
        assert color.startswith("#")

    def test_wraps_around(self):
        """Index > palette doit retourner une couleur valide (modulo)."""
        color_0 = get_community_color(0)
        color_10 = get_community_color(10)
        assert color_0 == color_10

    def test_different_indices_different_colors(self):
        colors = [get_community_color(i) for i in range(5)]
        assert len(set(colors)) > 1
