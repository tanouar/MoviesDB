"""Tests unitaires pour pipeline/read_marvel_wiki.py."""
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Ajout du dossier pipeline au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))

from read_marvel_wiki import clean_wiki_title, main  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_film_table(films):
    """Construit un DataFrame simulant une table Wikipedia de films MCU."""
    return pd.DataFrame(films, columns=["Film", "U.S. release date"])


def _make_response_mock(tables):
    """Crée un mock de requests.Response avec pd.read_html pré-rempli."""
    mock_resp = MagicMock()
    mock_resp.text = "<html></html>"
    return mock_resp, tables


# ---------------------------------------------------------------------------
# clean_wiki_title
# ---------------------------------------------------------------------------

class TestCleanWikiTitle:
    def test_removes_citation_brackets(self):
        assert clean_wiki_title("Iron Man[1]") == "Iron Man"

    def test_removes_multiple_citations(self):
        assert clean_wiki_title("Thor[2][d]") == "Thor"

    def test_replaces_thin_space(self):
        result = clean_wiki_title("Iron\u2009Man")
        assert "\u2009" not in result
        assert "Iron Man" == result

    def test_normalizes_whitespace(self):
        assert clean_wiki_title("Avengers   Endgame") == "Avengers Endgame"

    def test_strips_leading_trailing_spaces(self):
        assert clean_wiki_title("  Black Widow  ") == "Black Widow"

    def test_combined_cleaning(self):
        result = clean_wiki_title("  Doctor\u2009Strange[3]  ")
        assert result == "Doctor Strange"

    def test_non_string_none_passthrough(self):
        assert clean_wiki_title(None) is None

    def test_non_string_int_passthrough(self):
        assert clean_wiki_title(42) == 42

    def test_plain_string_unchanged(self):
        assert clean_wiki_title("The Avengers") == "The Avengers"

    def test_empty_string(self):
        assert clean_wiki_title("") == ""


# ---------------------------------------------------------------------------
# main — logique d'intégration (I/O mockée)
# ---------------------------------------------------------------------------

class TestMain:
    """Teste main() avec requests et to_csv entièrement mockés."""

    def _run_main(self, film_tables, today=None):
        """Lance main() en mockant requests, read_html et to_csv."""
        mock_resp = MagicMock()
        mock_resp.text = "<html></html>"

        fixed_today = today or pd.Timestamp("2025-01-01")

        with (
            patch("read_marvel_wiki.requests.get", return_value=mock_resp),
            patch("read_marvel_wiki.pd.read_html", return_value=film_tables),
            patch("read_marvel_wiki.pd.Timestamp.today", return_value=fixed_today),
            patch("pandas.DataFrame.to_csv") as mock_csv,
        ):
            main()

        return mock_csv

    def test_csv_written_once(self):
        tables = [_make_film_table([
            ("Iron Man", "May 2, 2008"),
            ("Thor", "May 6, 2011"),
        ])]
        mock_csv = self._run_main(tables)
        mock_csv.assert_called_once()

    def test_csv_path_correct(self):
        tables = [_make_film_table([("Iron Man", "May 2, 2008")])]
        mock_csv = self._run_main(tables)
        args, kwargs = mock_csv.call_args
        assert args[0] == "data/raw/marvel_films.csv"
        assert kwargs.get("index") is False

    def test_future_films_excluded(self):
        """Les films dont la date de sortie est dans le futur sont filtrés."""
        captured = {}

        def fake_to_csv(path, index=True):
            captured["df"] = None  # le df est l'instance appelante

        tables = [_make_film_table([
            ("Past Movie", "January 1, 2020"),
            ("Future Movie", "December 31, 2099"),
        ])]

        mock_resp = MagicMock()
        mock_resp.text = "<html></html>"
        fixed_today = pd.Timestamp("2025-01-01")

        written_frames = []

        original_to_csv = pd.DataFrame.to_csv

        def capturing_to_csv(self_df, path, index=True):
            written_frames.append(self_df.copy())

        with (
            patch("read_marvel_wiki.requests.get", return_value=mock_resp),
            patch("read_marvel_wiki.pd.read_html", return_value=tables),
            patch("read_marvel_wiki.pd.Timestamp.today", return_value=fixed_today),
            patch.object(pd.DataFrame, "to_csv", capturing_to_csv),
        ):
            main()

        assert len(written_frames) == 1
        df = written_frames[0]
        assert "Future Movie" not in df["film"].values
        assert "Past Movie" in df["film"].values

    def test_tba_release_date_excluded(self):
        """Les films avec 'TBA' comme date sont exclus."""
        tables = [_make_film_table([
            ("Released Film", "May 2, 2008"),
            ("Upcoming Film", "TBA"),
        ])]
        written_frames = []

        mock_resp = MagicMock()
        mock_resp.text = "<html></html>"
        fixed_today = pd.Timestamp("2025-01-01")

        def capturing_to_csv(self_df, path, index=True):
            written_frames.append(self_df.copy())

        with (
            patch("read_marvel_wiki.requests.get", return_value=mock_resp),
            patch("read_marvel_wiki.pd.read_html", return_value=tables),
            patch("read_marvel_wiki.pd.Timestamp.today", return_value=fixed_today),
            patch.object(pd.DataFrame, "to_csv", capturing_to_csv),
        ):
            main()

        df = written_frames[0]
        assert "Upcoming Film" not in df["film"].values

    def test_dash_release_date_excluded(self):
        """Les films avec '—' comme date sont exclus."""
        tables = [_make_film_table([
            ("Released Film", "May 2, 2008"),
            ("No Date Film", "—"),
        ])]
        written_frames = []

        mock_resp = MagicMock()
        mock_resp.text = "<html></html>"
        fixed_today = pd.Timestamp("2025-01-01")

        def capturing_to_csv(self_df, path, index=True):
            written_frames.append(self_df.copy())

        with (
            patch("read_marvel_wiki.requests.get", return_value=mock_resp),
            patch("read_marvel_wiki.pd.read_html", return_value=tables),
            patch("read_marvel_wiki.pd.Timestamp.today", return_value=fixed_today),
            patch.object(pd.DataFrame, "to_csv", capturing_to_csv),
        ):
            main()

        df = written_frames[0]
        assert "No Date Film" not in df["film"].values

    def test_release_year_column_present(self):
        """La colonne release_year est bien ajoutée au DataFrame CSV."""
        tables = [_make_film_table([("Iron Man", "May 2, 2008")])]
        written_frames = []

        mock_resp = MagicMock()
        mock_resp.text = "<html></html>"
        fixed_today = pd.Timestamp("2025-01-01")

        def capturing_to_csv(self_df, path, index=True):
            written_frames.append(self_df.copy())

        with (
            patch("read_marvel_wiki.requests.get", return_value=mock_resp),
            patch("read_marvel_wiki.pd.read_html", return_value=tables),
            patch("read_marvel_wiki.pd.Timestamp.today", return_value=fixed_today),
            patch.object(pd.DataFrame, "to_csv", capturing_to_csv),
        ):
            main()

        df = written_frames[0]
        assert "release_year" in df.columns
        assert int(df.loc[df["film"] == "Iron Man", "release_year"].iloc[0]) == 2008

    def test_citations_cleaned_in_film_names(self):
        """Les citations dans les titres de films (ex: Iron Man[1]) sont nettoyées."""
        tables = [_make_film_table([("Iron Man[1]", "May 2, 2008")])]
        written_frames = []

        mock_resp = MagicMock()
        mock_resp.text = "<html></html>"
        fixed_today = pd.Timestamp("2025-01-01")

        def capturing_to_csv(self_df, path, index=True):
            written_frames.append(self_df.copy())

        with (
            patch("read_marvel_wiki.requests.get", return_value=mock_resp),
            patch("read_marvel_wiki.pd.read_html", return_value=tables),
            patch("read_marvel_wiki.pd.Timestamp.today", return_value=fixed_today),
            patch.object(pd.DataFrame, "to_csv", capturing_to_csv),
        ):
            main()

        df = written_frames[0]
        assert "Iron Man" in df["film"].values
        assert "Iron Man[1]" not in df["film"].values

    def test_multiple_film_tables_concatenated(self):
        """Plusieurs tables Wikipedia sont bien concaténées."""
        tables = [
            _make_film_table([("Iron Man", "May 2, 2008")]),
            _make_film_table([("Thor", "May 6, 2011")]),
        ]
        written_frames = []

        mock_resp = MagicMock()
        mock_resp.text = "<html></html>"
        fixed_today = pd.Timestamp("2025-01-01")

        def capturing_to_csv(self_df, path, index=True):
            written_frames.append(self_df.copy())

        with (
            patch("read_marvel_wiki.requests.get", return_value=mock_resp),
            patch("read_marvel_wiki.pd.read_html", return_value=tables),
            patch("read_marvel_wiki.pd.Timestamp.today", return_value=fixed_today),
            patch.object(pd.DataFrame, "to_csv", capturing_to_csv),
        ):
            main()

        df = written_frames[0]
        films = df["film"].tolist()
        assert "Iron Man" in films
        assert "Thor" in films

    def test_non_film_tables_ignored(self):
        """Les tables sans colonne 'Film' sont ignorées."""
        non_film_table = pd.DataFrame({"Actor": ["RDJ"], "Role": ["Iron Man"]})
        film_table = _make_film_table([("Iron Man", "May 2, 2008")])
        tables = [non_film_table, film_table]
        written_frames = []

        mock_resp = MagicMock()
        mock_resp.text = "<html></html>"
        fixed_today = pd.Timestamp("2025-01-01")

        def capturing_to_csv(self_df, path, index=True):
            written_frames.append(self_df.copy())

        with (
            patch("read_marvel_wiki.requests.get", return_value=mock_resp),
            patch("read_marvel_wiki.pd.read_html", return_value=tables),
            patch("read_marvel_wiki.pd.Timestamp.today", return_value=fixed_today),
            patch.object(pd.DataFrame, "to_csv", capturing_to_csv),
        ):
            main()

        df = written_frames[0]
        assert "Actor" not in df.columns
        assert "film" in df.columns
