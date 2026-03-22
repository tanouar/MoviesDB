"""Fonctions d'aide pour l'interface utilisateur Streamlit."""
import streamlit as st


def sidebar_filters(all_labels, all_rel_types, movies_list=None):
    """Affiche les filtres dans la sidebar Streamlit.

    Args:
        all_labels: Liste de tous les labels disponibles
        all_rel_types: Liste de tous les types de relations disponibles
        movies_list: Liste optionnelle de films (dict avec 'id' et 'title')

    Returns:
        Tuple (selected_labels, selected_rels, selected_movie_id)
        avec les filtres sélectionnés
    """
    st.sidebar.header("Filtres du graphe")

    # Sélection d'un film spécifique
    selected_movie_id = None
    if movies_list and len(movies_list) > 0:
        st.sidebar.subheader("🎬 Sélection de film")

        # Créer une liste d'options pour le selectbox
        movie_options = ["-- Tous les films --"] + [
            movie["title"] for movie in movies_list
        ]

        selected_movie = st.sidebar.selectbox(
            "Choisissez un film",
            options=movie_options,
            index=0
        )

        # Récupérer l'ID du film sélectionné
        if selected_movie != "-- Tous les films --":
            for movie in movies_list:
                if movie["title"] == selected_movie:
                    selected_movie_id = movie["id"]
                    break

    st.sidebar.markdown("---")

    # Filtres existants
    selected_labels = st.sidebar.multiselect(
        "Sélectionnez les labels des nœuds",
        options=all_labels,
        default=all_labels
    )
    selected_rels = st.sidebar.multiselect(
        "Sélectionnez les types de relations",
        options=all_rel_types,
        default=all_rel_types
    )
    return selected_labels, selected_rels, selected_movie_id
