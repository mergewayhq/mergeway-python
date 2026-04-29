from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from mergeway_python.database import Database


EXAMPLE_ROOT = Path(__file__).resolve().parent / "fixtures" / "full"


class EndToEndTests(unittest.TestCase):
    def test_full_example_repository_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "repo"
            shutil.copytree(EXAMPLE_ROOT, workspace)

            database = Database(workspace / "mergeway.yaml")
            self.assertEqual(
                database.list_entities(), ["Comment", "Post", "Tag", "User"]
            )

            generated_path = database.generate_classes(
                workspace / "generated_models.py"
            )
            self.assertTrue(generated_path.exists())
            self.assertIsNotNone(database.classes_module)

            user = database.get("User", "user-alice")
            self.assertEqual(type(user).__name__, "User")
            self.assertEqual(user.email, "alice@example.com")
            self.assertEqual(user.roles, ["admin", "author"])

            users = database.export("User")
            self.assertEqual({item.id for item in users}, {"user-alice", "user-bob"})

            user_model = database.classes_module.User
            created = database.create(
                user_model,
                user_model(
                    id="user-cara",
                    name="Cara Example",
                    email="cara@example.com",
                    roles=["author"],
                ),
            )
            self.assertEqual(created.id, "user-cara")
            self.assertTrue((workspace / "data/users/user-cara.yaml").exists())

            updated = database.update(
                "User",
                "user-cara",
                {
                    "id": "user-cara",
                    "name": "Cara Updated",
                    "email": "cara@example.com",
                    "roles": ["author", "editor"],
                },
            )
            self.assertEqual(updated.name, "Cara Updated")
            self.assertEqual(updated.roles, ["author", "editor"])

            self.assertEqual(database.validate(), "validation succeeded")
            formatted = database.format(in_place=True)
            self.assertIn("data/users/user-cara.yaml", formatted)
            self.assertEqual(database.format(lint=True, in_place=False), "")

            exported = database.export()
            self.assertEqual(len(exported["User"]), 3)
            self.assertEqual(len(exported["Post"]), 1)
            self.assertEqual(exported["Comment"][0].post, "post-001")

            deleted = database.delete("User", "user-cara")
            self.assertEqual(deleted, "User user-cara deleted")
            self.assertFalse((workspace / "data/users/user-cara.yaml").exists())
