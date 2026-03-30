"""Application Streamlit pour l'exploration de graphes Neo4j/AuraDB."""
import os
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import streamlit.components.v1 as components
from modules.neo4j_connector import Neo4jConnector
from modules.graph_builder import build_pyvis_graph
from modules.graph_analyzer import analyze_graph, COMMUNITY_METHODS
from modules.ui_helpers import sidebar_filters

# Chargement des variables d'environnement depuis .env
load_dotenv()

# Obtenir le chemin absolu du dossier contenant app.py
APP_DIR = Path(__file__).parent

# ========================================
# Configuration Neo4j/AuraDB
# ========================================
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "password")

st.set_page_config(page_title="Marvel Cinematic Universe Graph", layout="wide")

# ========================================
# Injection du thème CSS Avengers: Doomsday
# ========================================
_css = (APP_DIR/"assets"/"css"/"avengers.css").read_text(encoding="utf-8")
st.markdown(f"<style>{_css}</style>", unsafe_allow_html=True)

st.title("Marvel Cinematic Universe")

# ========================================
# Compte à rebours — 16 décembre 2026 à 9h
# ========================================
_countdown_html = (
    APP_DIR / "components" / "countdown.html"
).read_text(encoding="utf-8")
components.html(_countdown_html, height=130)

# ========================================
# Connexion Neo4j + wrappers cachés
# ========================================
connector = Neo4jConnector(NEO4J_URI, NEO4J_USER, NEO4J_PASS)


@st.cache_data(ttl=300)
def cached_get_labels():
    return connector.get_all_labels()


@st.cache_data(ttl=300)
def cached_get_rel_types():
    return connector.get_all_relation_types()


@st.cache_data(ttl=300)
def cached_get_movies():
    return connector.get_all_movies()


@st.cache_data(ttl=120)
def cached_get_graph(labels, rel_types):
    return connector.get_graph(labels=list(labels), rel_types=list(rel_types))


@st.cache_data(ttl=120)
def cached_get_movie_graph(movie_id):
    return connector.get_movie_graph(movie_id)


@st.cache_data
def cached_analyze_graph(nodes, relationships, method):
    return analyze_graph(nodes, relationships, community_method=method)


@st.cache_data
def cached_build_graph(
    nodes, relationships, style_file,
    bc_scores, communities, bc_threshold
):
    return build_pyvis_graph(
        nodes,
        relationships,
        height="750px",
        style_file=style_file,
        debug=False,
        bc_scores=bc_scores,
        communities=communities,
        bc_threshold=bc_threshold,
    )


# Récupération dynamique des labels et types de relations
all_labels = cached_get_labels()
all_rel_types = cached_get_rel_types()

# Récupération de la liste des films
all_movies = cached_get_movies()

# Sidebar : filtres
selected_labels, selected_rels, selected_movie_id = sidebar_filters(
    all_labels,
    all_rel_types,
    all_movies
)

# Bouton pour rafraîchir le graphe
if st.sidebar.button("🔄 Rafraîchir le graphe"):
    st.cache_data.clear()
    st.rerun()

# Récupération des nœuds et relations filtrés
if selected_movie_id is not None:
    nodes, relationships = cached_get_movie_graph(selected_movie_id)
    st.sidebar.info("🎬 Affichage du graphe autour du film sélectionné")
else:
    nodes, relationships = cached_get_graph(
        tuple(selected_labels),
        tuple(selected_rels)
    )

st.sidebar.markdown(f"**Nœuds récupérés :** {len(nodes)}")
st.sidebar.markdown(f"**Relations récupérées :** {len(relationships)}")

# ========================================
# Section Analyse — Betweenness Centrality
# ========================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔬 Analyse topologique")
enable_analysis = st.sidebar.toggle(
    "Mode Analyse (Betweenness Centrality)", value=False
)
bc_threshold = 0.0
top_n = 5
community_method = "louvain"
if enable_analysis:
    _method_keys = list(COMMUNITY_METHODS.keys())
    method_label = st.sidebar.selectbox(
        "Algorithme de communautés",
        _method_keys,
        index=_method_keys.index("Louvain"),
    )
    community_method = COMMUNITY_METHODS[method_label]
    bc_threshold = st.sidebar.slider(
        "Seuil BC minimum", 0.0, 1.0, 0.1, 0.01
    )
    top_n = st.sidebar.slider("Top N nœuds ponts", 3, 30, 5)

# ========================================
# Section Auteur
# ========================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 👤 Auteur")
st.sidebar.markdown("**Tarik ANOUAR**")
_tarik_badge = (
    "[![LinkedIn](https://img.shields.io/badge/LinkedIn-Tarik%20ANOUAR"
    "-blue?logo=linkedin)](https://www.linkedin.com/in/anouartarik)"
)
st.sidebar.markdown(_tarik_badge)
st.sidebar.markdown("**Vaynee SUNGEELEE**")
_vaynee_badge = (
    "[![LinkedIn](https://img.shields.io/badge/LinkedIn-Vaynee%20SUNGEELEE"
    "-blue?logo=linkedin)](https://www.linkedin.com/in/vaynee-sungeelee/)"
)
st.sidebar.markdown(_vaynee_badge)

# Chemin absolu vers le fichier style.grass
STYLE_FILE = APP_DIR / "assets" / "style.grass"

if nodes:
    # --- Analyse topologique (optionnelle) ---
    bc_scores = None
    communities = None
    analysis = None
    if enable_analysis:
        analysis = cached_analyze_graph(
            nodes, relationships, community_method
        )
        bc_scores = analysis["bc"]
        communities = analysis["communities"]

    graph_html = cached_build_graph(
        nodes, relationships, str(STYLE_FILE),
        bc_scores, communities, bc_threshold,
    )

    # --- Tableau Top-N nœuds ponts ---
    if enable_analysis and analysis:
        st.markdown("#### 🌉 Top nœuds ponts (Betweenness Centrality)")
        top_bridges = analysis["top_bridges"][:top_n]
        id_to_name = {n["id"]: n.get("name") or n.get("title") or n["id"]
                      for n in nodes}
        id_to_label = {}
        for n in nodes:
            lbl = n.get("labels") or n.get("label") or "?"
            if isinstance(lbl, list):
                lbl = ", ".join(lbl)
            id_to_label[n["id"]] = lbl
        nb_communities = len(set(communities.values()))
        col1, col2, col3 = st.columns(3)
        col1.metric("Nœuds analysés", len(nodes))
        col2.metric("Sous-graphes détectés", nb_communities)
        col3.metric("Nœuds ponts (seuil)", sum(
            1 for _, s in analysis["top_bridges"] if s >= bc_threshold
        ))
        table_data = [
            {
                "Rang": i + 1,
                "Nom": id_to_name.get(nid, nid),
                "Type": id_to_label.get(nid, "?"),
                "Score BC": round(score, 5),
            }
            for i, (nid, score) in enumerate(top_bridges)
        ]
        st.dataframe(table_data, use_container_width=True)

    # Affiche le graphe
    components.html(graph_html, height=750, scrolling=True)
else:
    st.warning(
        "Aucun nœud ou relation ne correspond aux filtres sélectionnés."
    )
