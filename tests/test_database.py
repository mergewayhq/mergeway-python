from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mergeway_python.codegen import generate_classes
from mergeway_python.database import Database

from tests.test_codegen import FakeDatabase, SCHEMAS


class DatabaseTests(unittest.TestCase):
    def test_database_returns_generated_models_and_serializes_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            generated_path = generate_classes(
                FakeDatabase(), Path(tmpdir) / "generated_models.py"
            )
            payload_calls: list[tuple[list[str], dict, str | None]] = []

            def fake_run(
                self: Database,
                *args: str,
                output_format: str | None = None,
                yes: bool = False,
            ) -> str:
                if args[:2] == ("get", "user-1"):
                    return json.dumps({"id": "user-1", "display-name": "Alice"})
                if args[:1] == ("export",):
                    return json.dumps(
                        {"User": [{"id": "user-1", "display-name": "Alice"}]}
                    )
                if args[:2] == ("delete", "user-1"):
                    assert yes
                    return "User user-1 deleted"
                return ""

            def fake_run_with_payload(
                self: Database,
                args: list[str],
                payload: dict,
                *,
                object_id: str | None = None,
            ) -> str:
                payload_calls.append((args, payload, object_id))
                return ""

            with (
                patch.object(Database, "_run", new=fake_run),
                patch.object(Database, "_run_with_payload", new=fake_run_with_payload),
                patch.object(
                    Database, "entity_schema", new=lambda self, entity: SCHEMAS[entity]
                ),
            ):
                database = Database(
                    "/tmp/repo/mergeway.yaml", classes_module=generated_path
                )
                user_model = database.classes_module.User

                user = database.get("User", "user-1")
                self.assertIsInstance(user, user_model)
                self.assertEqual(user.display_name, "Alice")

                users = database.list(user_model)
                self.assertEqual(len(users), 1)
                self.assertIsInstance(users[0], user_model)

                created = database.create(
                    user_model, user_model(id="user-1", display_name="Alice")
                )
                self.assertIsInstance(created, user_model)
                self.assertEqual(
                    payload_calls[0],
                    (
                        ["create", "--type", "User"],
                        {"id": "user-1", "display-name": "Alice"},
                        None,
                    ),
                )

                updated = database.update(
                    "User", "user-1", {"display-name": "Alicia"}, merge=True
                )
                self.assertIsInstance(updated, user_model)
                self.assertEqual(
                    payload_calls[1],
                    (
                        ["update", "--type", "User", "--id", "user-1", "--merge"],
                        {"display-name": "Alicia"},
                        None,
                    ),
                )

                deleted = database.delete("User", "user-1")
                self.assertEqual(deleted, "User user-1 deleted")
