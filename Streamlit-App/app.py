"""Application Streamlit pour l'exploration de graphes Neo4j/AuraDB."""
import os
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import streamlit.components.v1 as components
from modules.neo4j_connector import Neo4jConnector
from modules.graph_builder import build_pyvis_graph
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

# Connexion à Neo4j
connector = Neo4jConnector(NEO4J_URI, NEO4J_USER, NEO4J_PASS)

# Récupération dynamique des labels et types de relations
all_labels = connector.get_all_labels()
all_rel_types = connector.get_all_relation_types()

# Récupération de la liste des films
all_movies = connector.get_all_movies()

# Sidebar : filtres
selected_labels, selected_rels, selected_movie_id = sidebar_filters(
    all_labels,
    all_rel_types,
    all_movies
)

# Bouton pour rafraîchir le graphe
if st.sidebar.button("🔄 Rafraîchir le graphe"):
    st.rerun()  # ⚡ Remplace st.experimental_rerun

# Récupération des nœuds et relations filtrés
if selected_movie_id is not None:
    # Si un film est sélectionné, afficher son graphe
    nodes, relationships = connector.get_movie_graph(selected_movie_id)
    st.sidebar.info(f"🎬 Affichage du graphe autour du film sélectionné")
else:
    # Sinon, afficher le graphe avec les filtres standards
    nodes, relationships = connector.get_graph(
        labels=selected_labels,
        rel_types=selected_rels
    )

st.sidebar.markdown(f"**Nœuds récupérés :** {len(nodes)}")
st.sidebar.markdown(f"**Relations récupérées :** {len(relationships)}")

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
    result = build_pyvis_graph(
        nodes,
        relationships,
        height="750px",
        style_file=STYLE_FILE,
        debug=False
    )
    graph_html = result

    # Affiche le graphe
    components.html(graph_html, height=750, scrolling=True)
else:
    st.warning(
        "Aucun nœud ou relation ne correspond aux filtres sélectionnés."
    )
