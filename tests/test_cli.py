from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from mergeway_python import cli


class CLITests(unittest.TestCase):
    def test_generate_accepts_repository_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "repo"
            root.mkdir()
            output = root / "models.py"
            config = root / "mergeway.yaml"

            with patch("mergeway_python.cli.Database") as database_cls:
                database = database_cls.return_value
                database.generate_classes.return_value = output

                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    exit_code = cli.main(["generate", "--root", str(root), str(output)])

                self.assertEqual(exit_code, 0)
                database_cls.assert_called_once_with(
                    config,
                    cli_binary="mergeway-cli",
                )
                database.generate_classes.assert_called_once_with(output)
                self.assertEqual(stdout.getvalue().strip(), str(output))

    def test_generate_accepts_explicit_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "repo"
            root.mkdir()
            output = root / "models.py"
            config = root / "custom-mergeway.yaml"

            with patch("mergeway_python.cli.Database") as database_cls:
                database = database_cls.return_value
                database.generate_classes.return_value = output

                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    exit_code = cli.main(
                        ["generate", "--config", str(config), str(output)]
                    )

                self.assertEqual(exit_code, 0)
                database_cls.assert_called_once_with(
                    config,
                    cli_binary="mergeway-cli",
                )
                self.assertEqual(stdout.getvalue().strip(), str(output))
