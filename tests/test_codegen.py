from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from mergeway.codegen import generate_classes


SCHEMAS = {
    "User": {
        "Identifier": {"Field": "id"},
        "Fields": {
            "id": {
                "Type": "string",
                "Required": True,
                "Repeated": False,
                "ReferenceTypes": None,
            },
            "display-name": {
                "Type": "string",
                "Required": True,
                "Repeated": False,
                "ReferenceTypes": None,
            },
            "active": {
                "Type": "boolean",
                "Required": False,
                "Repeated": False,
                "ReferenceTypes": None,
            },
        },
        "FieldOrder": ["id", "display-name", "active"],
    },
    "Post": {
        "Identifier": {"Field": "id"},
        "Fields": {
            "id": {
                "Type": "string",
                "Required": True,
                "Repeated": False,
                "ReferenceTypes": None,
            },
            "title": {
                "Type": "string",
                "Required": True,
                "Repeated": False,
                "ReferenceTypes": None,
            },
            "status": {
                "Type": "enum",
                "Required": True,
                "Repeated": False,
                "ReferenceTypes": None,
                "Enum": ["DRAFT", "PUBLISHED"],
            },
            "owner": {
                "Type": "User | Team",
                "Required": False,
                "Repeated": False,
                "ReferenceTypes": ["User", "Team"],
            },
            "metadata": {
                "Type": "object",
                "Required": False,
                "Repeated": False,
                "ReferenceTypes": None,
                "Properties": {
                    "editor": {
                        "Type": "User",
                        "Required": False,
                        "Repeated": False,
                        "ReferenceTypes": ["User"],
                    },
                    "review-score": {
                        "Type": "number",
                        "Required": False,
                        "Repeated": False,
                        "ReferenceTypes": None,
                    },
                },
                "PropertyOrder": ["editor", "review-score"],
            },
            "contacts": {
                "Type": "object",
                "Required": False,
                "Repeated": True,
                "ReferenceTypes": None,
                "Properties": {
                    "label": {
                        "Type": "string",
                        "Required": True,
                        "Repeated": False,
                        "ReferenceTypes": None,
                    },
                    "email-address": {
                        "Type": "string",
                        "Required": False,
                        "Repeated": False,
                        "ReferenceTypes": None,
                    },
                },
                "PropertyOrder": ["label", "email-address"],
            },
        },
        "FieldOrder": ["id", "title", "status", "owner", "metadata", "contacts"],
    },
}


class FakeDatabase:
    def list_entities(self) -> list[str]:
        return ["User", "Post"]

    def entity_schema(self, entity: str) -> dict:
        return SCHEMAS[entity]


class CodegenTests(unittest.TestCase):
    def test_generated_models_round_trip_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = generate_classes(
                FakeDatabase(), Path(tmpdir) / "generated_models.py"
            )
            spec = importlib.util.spec_from_file_location(
                "test_generated_models", module_path
            )
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            user = module.User(id="user-1", display_name="Alice", active=True)
            self.assertEqual(
                user.to_payload(),
                {"id": "user-1", "display-name": "Alice", "active": True},
            )

            post = module.Post.from_payload(
                {
                    "id": "post-1",
                    "title": "Launch",
                    "status": "DRAFT",
                    "owner": "user-1",
                    "metadata": {"editor": "user-1", "review-score": 4.5},
                    "contacts": [
                        {"label": "Press", "email-address": "press@example.com"}
                    ],
                }
            )

            self.assertEqual(post.status, module.PostStatusEnum.DRAFT)
            self.assertEqual(post.metadata.review_score, 4.5)
            self.assertEqual(post.contacts[0].email_address, "press@example.com")
            self.assertEqual(
                post.to_payload(),
                {
                    "id": "post-1",
                    "title": "Launch",
                    "status": "DRAFT",
                    "owner": "user-1",
                    "metadata": {"editor": "user-1", "review-score": 4.5},
                    "contacts": [
                        {"label": "Press", "email-address": "press@example.com"}
                    ],
                },
            )
            self.assertIs(module.ENTITY_REGISTRY["Post"], module.Post)
