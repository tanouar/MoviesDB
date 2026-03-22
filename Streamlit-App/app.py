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

st.set_page_config(page_title="Neo4j Graph Explorer", layout="wide")
st.title("🌐 Neo4j Graph Explorer - Interactive")

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

# Chemin absolu vers le fichier style.grass (fonctionne en local et sur Streamlit Cloud)
STYLE_FILE = APP_DIR / "assets" / "style.grass"

if nodes:
    result = build_pyvis_graph(
        nodes,
        relationships,
        height="750px",
        style_file=STYLE_FILE,
        debug=True
    )
    # result est un dict avec 'html' et 'debug'
    graph_html = result["html"]
    debug_info = result["debug"]

    # Affiche d'abord le debug (panneau repliable)
    with st.expander("Debug styles par noeud (ouvrir pour voir)"):
        st.write(
            "Extrait des premiers nœuds et le style appliqué "
            "(id, raw_labels, chosen_label, applied_style_color)"
        )
        # On affiche une version concise
        # version robuste : utilise les clés présentes dans debug_info
        short = []
        for d in debug_info:
            short.append({
                "id": d.get("id"),
                "raw_labels": d.get("raw_labels"),
                "chosen_label": d.get("chosen_label"),
                "color": d.get(
                    "bg_color",
                    d.get("applied_style_color", None)
                ),
                "caption": d.get("caption")
            })
        st.json(short)

    # Affiche le graphe
    components.html(graph_html, height=750, scrolling=True)
else:
    st.warning(
        "Aucun nœud ou relation ne correspond aux filtres sélectionnés."
    )
