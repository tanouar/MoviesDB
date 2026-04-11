"""Tests unitaires pour pipeline/run_pipeline.py."""
import argparse
import gzip
import os
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Définir la variable d'environnement AVANT l'import du module
os.environ.setdefault("MYSQL_ROOT_PASSWORD", "test_password")

# Ajout du dossier pipeline au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))

import run_pipeline  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_proc(returncode=0, stdout="", stderr=""):
    """Crée un objet CompletedProcess simulé."""
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = stdout
    mock.stderr = stderr
    return mock


def _make_args(createdb=False, runqueries=False,
               createcsvs=False, debug=False):
    return argparse.Namespace(
        createdb=createdb,
        runqueries=runqueries,
        createcsvs=createcsvs,
        debug=debug,
    )


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------

class TestParseArgs:
    def test_default_all_false(self):
        with patch("sys.argv", ["run_pipeline.py"]):
            args = run_pipeline.parse_args()
        assert args.debug is False
        assert args.createdb is False
        assert args.createcsvs is False
        assert args.runqueries is False

    def test_long_debug_flag(self):
        with patch("sys.argv", ["run_pipeline.py", "--debug"]):
            args = run_pipeline.parse_args()
        assert args.debug is True

    def test_long_createdb_flag(self):
        with patch("sys.argv", ["run_pipeline.py", "--createdb"]):
            args = run_pipeline.parse_args()
        assert args.createdb is True

    def test_long_createcsvs_flag(self):
        with patch("sys.argv", ["run_pipeline.py", "--createcsvs"]):
            args = run_pipeline.parse_args()
        assert args.createcsvs is True

    def test_long_runqueries_flag(self):
        with patch("sys.argv", ["run_pipeline.py", "--runqueries"]):
            args = run_pipeline.parse_args()
        assert args.runqueries is True

    def test_short_flags_combined(self):
        with patch("sys.argv", ["run_pipeline.py", "-d", "-db", "-csv", "-q"]):
            args = run_pipeline.parse_args()
        assert args.debug is True
        assert args.createdb is True
        assert args.createcsvs is True
        assert args.runqueries is True


# ---------------------------------------------------------------------------
# run_command
# ---------------------------------------------------------------------------

class TestRunCommand:
    def test_success_returns_result(self):
        mock_result = _make_proc(returncode=0, stdout="ok")
        with patch("subprocess.run", return_value=mock_result):
            result = run_pipeline.run_command(["echo", "hello"])
        assert result.returncode == 0

    def test_failure_check_true_raises_runtime_error(self):
        mock_result = _make_proc(returncode=1, stderr="error")
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="Command failed"):
                run_pipeline.run_command(["bad_cmd"])

    def test_failure_check_false_returns_result(self):
        mock_result = _make_proc(returncode=1, stderr="error")
        with patch("subprocess.run", return_value=mock_result):
            result = run_pipeline.run_command(["bad_cmd"], check=False)
        assert result.returncode == 1

    def test_calls_subprocess_run_with_given_cmd(self):
        mock_result = _make_proc(returncode=0)
        with patch("subprocess.run", return_value=mock_result) as mock_sub:
            run_pipeline.run_command(["echo", "test"])
        args, kwargs = mock_sub.call_args
        assert args[0] == ["echo", "test"]

    def test_capture_output_enabled(self):
        mock_result = _make_proc(returncode=0)
        with patch("subprocess.run", return_value=mock_result) as mock_sub:
            run_pipeline.run_command(["ls"])
        _, kwargs = mock_sub.call_args
        assert kwargs.get("capture_output") is True


# ---------------------------------------------------------------------------
# copy_tsv_to_container
# ---------------------------------------------------------------------------

class TestCopyTsvToContainer:
    def test_copies_six_files(self):
        with patch("subprocess.run", return_value=_make_proc()) as mock_run:
            run_pipeline.copy_tsv_to_container()
        assert mock_run.call_count == 6  # 5 TSV + 1 CSV Marvel

    def test_uses_docker_cp(self):
        with patch("subprocess.run", return_value=_make_proc()) as mock_run:
            run_pipeline.copy_tsv_to_container()
        for call_args in mock_run.call_args_list:
            cmd = call_args[0][0]
            assert cmd[0] == "docker"
            assert cmd[1] == "cp"

    def test_copies_marvel_csv(self):
        with patch("subprocess.run", return_value=_make_proc()) as mock_run:
            run_pipeline.copy_tsv_to_container()
        all_cmds = [call_args[0][0] for call_args in mock_run.call_args_list]
        assert any("marvel_films.csv" in " ".join(map(str, cmd))
                   for cmd in all_cmds)


# ---------------------------------------------------------------------------
# execute_sql_file
# ---------------------------------------------------------------------------

class TestExecuteSqlFile:
    def test_success(self, tmp_path):
        sql_file = tmp_path / "test.sql"
        sql_file.write_bytes(b"SELECT 1;")

        exec_result = _make_proc(returncode=0)

        with patch("subprocess.run", return_value=exec_result), \
                patch("time.time", side_effect=[0, 31]):
            run_pipeline.execute_sql_file(sql_file)  # ne lève pas

    def test_failure_raises_runtime_error(self, tmp_path):
        sql_file = tmp_path / "bad.sql"
        sql_file.write_bytes(b"BAD SQL;")

        exec_result = _make_proc(returncode=1, stderr="SQL error")

        def _fake_time(_calls=[0]):
            _calls[0] += 1
            return 0.0 if _calls[0] == 1 else 100.0

        with patch("subprocess.run", return_value=exec_result), \
                patch("time.time", side_effect=_fake_time):
            with pytest.raises(RuntimeError, match="SQL execution failed"):
                run_pipeline.execute_sql_file(sql_file)

    def test_error_message_contains_filename(self, tmp_path):
        sql_file = tmp_path / "myfile.sql"
        sql_file.write_bytes(b"SELECT 0;")

        exec_result = _make_proc(returncode=1, stderr="err")

        def _fake_time(_calls=[0]):
            _calls[0] += 1
            return 0.0 if _calls[0] == 1 else 100.0

        with patch("subprocess.run", return_value=exec_result), \
                patch("time.time", side_effect=_fake_time):
            with pytest.raises(RuntimeError, match="myfile.sql"):
                run_pipeline.execute_sql_file(sql_file)

    def test_socket_ready_breaks_loop(self, tmp_path):
        """La boucle s'arrête dès que le socket répond avec 'ready'."""
        sql_file = tmp_path / "test.sql"
        sql_file.write_bytes(b"SELECT 1;")

        sock_result = _make_proc(returncode=0, stdout="ready")
        exec_result = _make_proc(returncode=0)

        with patch("subprocess.run",
                   side_effect=[sock_result, exec_result]) as mock_run, \
                patch("time.time", return_value=0):
            run_pipeline.execute_sql_file(sql_file)

        # sock check + mysql exec = 2 appels
        assert mock_run.call_count == 2


# ---------------------------------------------------------------------------
# cleanup
# ---------------------------------------------------------------------------

class TestCleanup:
    def test_calls_docker_compose_down(self):
        with patch("run_pipeline.run_command") as mock_cmd:
            run_pipeline.cleanup()
        cmd = mock_cmd.call_args[0][0]
        assert "down" in cmd
        assert "compose" in cmd

    def test_uses_compose_file_path(self):
        with patch("run_pipeline.run_command") as mock_cmd:
            run_pipeline.cleanup()
        cmd = mock_cmd.call_args[0][0]
        assert str(run_pipeline.COMPOSE_FILE) in cmd


# ---------------------------------------------------------------------------
# update_csv_file
# ---------------------------------------------------------------------------

class TestUpdateCsvFile:
    def _write_raw_csv(self, tmp_path, name, rows):
        """Écrit un CSV sans en-tête (tel que généré par MySQL OUTFILE)."""
        path = tmp_path / name
        with open(path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(",".join(str(v) for v in row) + "\n")
        return path

    def test_movies_file_has_correct_columns(self, tmp_path):
        path = self._write_raw_csv(
            tmp_path, "marvel_movies.csv",
            [["tt001", "Avengers", "Action", 2012, 143]]
        )
        run_pipeline.update_csv_file(path)
        result = pd.read_csv(path)
        assert list(result.columns) == [
            "title_id", "primary_title", "genres",
            "start_year", "runtime_minutes"
        ]

    def test_actors_file_has_correct_columns(self, tmp_path):
        path = self._write_raw_csv(
            tmp_path, "marvel_actors.csv",
            [["nm001", "Robert Downey Jr.", 1965, ""]]
        )
        run_pipeline.update_csv_file(path)
        result = pd.read_csv(path)
        assert list(result.columns) == [
            "person_id", "person_name", "born", "died"
        ]

    def test_characters_file_normalizes_title_case(self, tmp_path):
        path = self._write_raw_csv(
            tmp_path, "marvel_characters.csv",
            [["iron man"], ["BLACK WIDOW"], ["spider-man"]]
        )
        run_pipeline.update_csv_file(path)
        result = pd.read_csv(path)
        assert result["character_name"].iloc[0] == "Iron Man"
        assert result["character_name"].iloc[1] == "Black Widow"
        assert result["character_name"].iloc[2] == "Spider-Man"

    def test_character_appears_in_movie_columns(self, tmp_path):
        path = self._write_raw_csv(
            tmp_path, "marvel_character_appears_in_movie.csv",
            [["tt001", "Iron Man"]]
        )
        run_pipeline.update_csv_file(path)
        result = pd.read_csv(path)
        assert list(result.columns) == ["title_id", "character_name"]

    def test_person_plays_character_columns(self, tmp_path):
        path = self._write_raw_csv(
            tmp_path, "marvel_person_plays_character.csv",
            [["nm001", "Iron Man"]]
        )
        run_pipeline.update_csv_file(path)
        result = pd.read_csv(path)
        assert list(result.columns) == ["person_id", "character_name"]

    def test_person_produces_movie_columns(self, tmp_path):
        path = self._write_raw_csv(
            tmp_path, "marvel_person_produces_movie.csv",
            [["tt001", "nm001"]]
        )
        run_pipeline.update_csv_file(path)
        result = pd.read_csv(path)
        assert list(result.columns) == ["title_id", "person_id"]

    def test_person_directs_movie_columns(self, tmp_path):
        path = self._write_raw_csv(
            tmp_path, "marvel_person_directs_movie.csv",
            [["tt001", "nm001"]]
        )
        run_pipeline.update_csv_file(path)
        result = pd.read_csv(path)
        assert list(result.columns) == ["title_id", "person_id"]

    def test_unknown_file_raises_value_error(self, tmp_path):
        path = self._write_raw_csv(
            tmp_path, "unknown_random_file.csv",
            [["x", "y"]]
        )
        with pytest.raises(ValueError, match="No column mapping found"):
            run_pipeline.update_csv_file(path)

    def test_file_is_overwritten_with_header(self, tmp_path):
        """Le fichier résultant doit contenir un vrai en-tête CSV."""
        path = self._write_raw_csv(
            tmp_path, "marvel_movies.csv",
            [["tt001", "Avengers", "Action", 2012, 143]]
        )
        run_pipeline.update_csv_file(path)
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        assert "title_id" in first_line


# ---------------------------------------------------------------------------
# download_files
# ---------------------------------------------------------------------------

class TestDownloadFiles:
    def _make_gz_bytes(self, content: bytes = b"col\nval") -> bytes:
        buf = BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
            gz.write(content)
        return buf.getvalue()

    _FILE_NAMES = [
        "name.basics",
        "title.basics",
        "title.episode",
        "title.principals",
        "title.ratings",
    ]

    def test_no_http_request_when_gz_exists(self, tmp_path):
        """Aucune requête HTTP si tous les .gz sont déjà présents."""
        gz_bytes = self._make_gz_bytes()
        with patch.object(run_pipeline, "PROJECT_ROOT", tmp_path):
            raw_dir = tmp_path / "data" / "raw"
            raw_dir.mkdir(parents=True)
            for name in self._FILE_NAMES:
                (raw_dir / f"{name}.tsv.gz").write_bytes(gz_bytes)
                (raw_dir / f"{name}.tsv").write_bytes(b"col\nval")

            with patch("requests.get") as mock_get:
                run_pipeline.download_files()

        mock_get.assert_not_called()

    def test_tsv_extracted_when_missing(self, tmp_path):
        """Les .tsv sont créés si le .gz existe mais pas le .tsv."""
        gz_bytes = self._make_gz_bytes()
        with patch.object(run_pipeline, "PROJECT_ROOT", tmp_path):
            raw_dir = tmp_path / "data" / "raw"
            raw_dir.mkdir(parents=True)
            for name in self._FILE_NAMES:
                (raw_dir / f"{name}.tsv.gz").write_bytes(gz_bytes)
                # Pas de .tsv → extraction attendue

            with patch("requests.get"):
                run_pipeline.download_files()

            for name in self._FILE_NAMES:
                assert (raw_dir / f"{name}.tsv").exists()

    def test_http_request_when_gz_missing(self, tmp_path):
        """Une requête HTTP est faite si le .gz n'existe pas."""
        gz_bytes = self._make_gz_bytes()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raw.read.return_value = gz_bytes

        with patch.object(run_pipeline, "PROJECT_ROOT", tmp_path):
            raw_dir = tmp_path / "data" / "raw"
            raw_dir.mkdir(parents=True)

            with patch("requests.get", return_value=mock_response) as mock_get:
                run_pipeline.download_files()

        assert mock_get.call_count == len(self._FILE_NAMES)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

class TestMain:
    def test_no_flag_activates_all_steps(self):
        """Sans flag explicite, les trois étapes sont activées."""
        args = _make_args()  # tous à False

        # run_command lève pour sortir de main() dès après l'activation des flags  # noqa: E501
        with patch("run_pipeline.parse_args", return_value=args), \
                patch("run_pipeline.setup_logger", return_value=MagicMock()), \
                patch("run_pipeline.run_command",
                      side_effect=RuntimeError("stop early")), \
                patch("run_pipeline.cleanup"):
            run_pipeline.main()

        assert args.createdb is True
        assert args.runqueries is True
        assert args.createcsvs is True

    def test_docker_failure_exits_early(self):
        """Si Docker ne démarre pas, main retourne sans lancer le pipeline."""
        args = _make_args(createdb=True)

        with patch("run_pipeline.parse_args", return_value=args), \
                patch("run_pipeline.setup_logger", return_value=MagicMock()), \
                patch("run_pipeline.run_command",
                      side_effect=RuntimeError("Docker failed")), \
                patch("run_pipeline.download_files") as mock_dl, \
                patch("run_pipeline.cleanup"):
            run_pipeline.main()

        mock_dl.assert_not_called()

    def test_createdb_calls_download_and_copy(self):
        """L'étape createdb déclenche download_files et copy_tsv_to_container."""  # noqa: E501
        args = _make_args(createdb=True)

        with patch("run_pipeline.parse_args", return_value=args), \
                patch("run_pipeline.setup_logger", return_value=MagicMock()), \
                patch("run_pipeline.run_command"), \
                patch("run_pipeline.download_files") as mock_dl, \
                patch("run_pipeline.copy_tsv_to_container") as mock_copy, \
                patch("run_pipeline.execute_sql_file"), \
                patch("run_pipeline.cleanup"):
            run_pipeline.main()

        mock_dl.assert_called_once()
        mock_copy.assert_called_once()

    def test_cleanup_always_called(self):
        """cleanup() doit être appelée même si les étapes se passent bien."""
        args = _make_args(createdb=True, runqueries=False, createcsvs=False)

        with patch("run_pipeline.parse_args", return_value=args), \
                patch("run_pipeline.setup_logger", return_value=MagicMock()), \
                patch("run_pipeline.run_command"), \
                patch("run_pipeline.download_files"), \
                patch("run_pipeline.copy_tsv_to_container"), \
                patch("run_pipeline.execute_sql_file"), \
                patch("run_pipeline.cleanup") as mock_cleanup:
            run_pipeline.main()

        mock_cleanup.assert_called_once()

    def test_debug_flag_sets_debug_level(self):
        """Le flag --debug configure le logger en DEBUG."""
        import logging
        args = _make_args(debug=True)

        with patch("run_pipeline.parse_args", return_value=args), \
                patch("run_pipeline.setup_logger",
                      return_value=MagicMock()) as mock_logger, \
                patch("run_pipeline.run_command",
                      side_effect=RuntimeError("stop early")), \
                patch("run_pipeline.cleanup"):
            run_pipeline.main()

        mock_logger.assert_called_once_with(level=logging.DEBUG)
