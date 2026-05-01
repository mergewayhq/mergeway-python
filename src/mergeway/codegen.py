"""Schema-driven class generation for Mergeway repositories."""

from __future__ import annotations

from dataclasses import dataclass
from keyword import iskeyword
from pathlib import Path
from typing import Any


PRIMITIVE_TYPES = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
}


@dataclass(frozen=True)
class RenderedField:
    name: str
    annotation: str
    required: bool


class ModelGenerator:
    def __init__(self, database: Any):
        self.database = database
        self.helper_blocks: list[str] = []
        self.helper_names: list[str] = []
        self.emitted_helpers: set[str] = set()

    def render(self) -> str:
        entity_names = self.database.list_entities()
        entity_blocks = [
            self._render_entity(entity_name) for entity_name in entity_names
        ]
        public_names = [*self.helper_names, *entity_names, "ENTITY_REGISTRY"]
        imports = [
            "from __future__ import annotations",
            "from dataclasses import dataclass",
            "from enum import Enum",
            "from typing import Any, ClassVar",
            "from mergeway.models import GeneratedModel",
        ]
        sections = [
            '"""Generated Mergeway entity models."""',
            "\n".join(imports),
            *self.helper_blocks,
            *entity_blocks,
            self._render_registry(entity_names),
            f"__all__ = {public_names!r}",
        ]
        return "\n\n".join(sections) + "\n"

    def _render_registry(self, entity_names: list[str]) -> str:
        lines = ["ENTITY_REGISTRY = {"]
        for entity_name in entity_names:
            lines.append(f"    {entity_name!r}: {entity_name},")
        lines.append("}")
        return "\n".join(lines)

    def _render_entity(self, entity_name: str) -> str:
        schema = self.database.entity_schema(entity_name)
        return self._render_model_class(
            class_name=entity_name,
            fields_map=schema.get("Fields") or {},
            field_order=schema.get("FieldOrder") or [],
            entity_name=entity_name,
            helper_prefix=[entity_name],
        )

    def _render_model_class(
        self,
        *,
        class_name: str,
        fields_map: dict[str, Any],
        field_order: list[str],
        entity_name: str | None,
        helper_prefix: list[str],
    ) -> str:
        ordered_fields = self._ordered_field_names(fields_map, field_order)
        rendered_fields: list[RenderedField] = []
        aliases: dict[str, str] = {}

        for field_name in ordered_fields:
            field_schema = fields_map[field_name]
            python_name = self._safe_identifier(field_name)
            if python_name != field_name:
                aliases[python_name] = field_name
            annotation = self._annotation_for_field(
                field_name=field_name,
                field_schema=field_schema,
                helper_prefix=[*helper_prefix, field_name],
            )
            rendered_fields.append(
                RenderedField(
                    name=python_name,
                    annotation=annotation,
                    required=bool(field_schema.get("Required")),
                )
            )

        rendered_fields = [
            *[item for item in rendered_fields if item.required],
            *[item for item in rendered_fields if not item.required],
        ]

        lines = ["@dataclass(slots=True)", f"class {class_name}(GeneratedModel):"]
        if entity_name is not None:
            lines.append(
                f"    __mergeway_entity_name__: ClassVar[str] = {entity_name!r}"
            )
        lines.append(
            f"    __mergeway_field_aliases__: ClassVar[dict[str, str]] = {aliases!r}"
        )

        if not rendered_fields:
            lines.append("    pass")
            return "\n".join(lines)

        for rendered_field in rendered_fields:
            field_line = f"    {rendered_field.name}: {rendered_field.annotation}"
            if not rendered_field.required:
                field_line += " = None"
            lines.append(field_line)
        return "\n".join(lines)

    def _annotation_for_field(
        self,
        *,
        field_name: str,
        field_schema: dict[str, Any],
        helper_prefix: list[str],
    ) -> str:
        base_type = self._base_annotation(field_name, field_schema, helper_prefix)
        if field_schema.get("Repeated"):
            base_type = f"list[{base_type}]"
        if not field_schema.get("Required"):
            base_type = f"{base_type} | None"
        return base_type

    def _base_annotation(
        self,
        field_name: str,
        field_schema: dict[str, Any],
        helper_prefix: list[str],
    ) -> str:
        field_type = field_schema.get("Type", "")

        if field_type == "enum":
            helper_name = self._helper_name(helper_prefix, suffix="Enum")
            self._ensure_enum(helper_name, field_schema.get("Enum") or [])
            return helper_name

        if field_type == "object":
            helper_name = self._helper_name(helper_prefix)
            self._ensure_object_class(
                helper_name,
                field_schema.get("Properties") or {},
                field_schema.get("PropertyOrder") or [],
                helper_prefix,
            )
            return helper_name

        if field_schema.get("ReferenceTypes"):
            return "str"

        return PRIMITIVE_TYPES.get(field_type, "Any")

    def _ensure_enum(self, helper_name: str, values: list[Any]) -> None:
        if helper_name in self.emitted_helpers:
            return
        self.emitted_helpers.add(helper_name)
        self.helper_names.append(helper_name)

        lines = [f"class {helper_name}(str, Enum):"]
        if not values:
            lines.append("    pass")
        for value in values:
            lines.append(f"    {self._enum_member_name(value)} = {value!r}")
        self.helper_blocks.append("\n".join(lines))

    def _ensure_object_class(
        self,
        helper_name: str,
        fields_map: dict[str, Any],
        field_order: list[str],
        helper_prefix: list[str],
    ) -> None:
        if helper_name in self.emitted_helpers:
            return
        self.emitted_helpers.add(helper_name)
        self.helper_names.append(helper_name)
        self.helper_blocks.append(
            self._render_model_class(
                class_name=helper_name,
                fields_map=fields_map,
                field_order=field_order,
                entity_name=None,
                helper_prefix=helper_prefix,
            )
        )

    def _ordered_field_names(
        self,
        fields_map: dict[str, Any],
        field_order: list[str],
    ) -> list[str]:
        seen: set[str] = set()
        ordered = [name for name in field_order if name in fields_map]
        seen.update(ordered)
        ordered.extend(sorted(name for name in fields_map if name not in seen))
        return ordered

    def _helper_name(self, parts: list[str], suffix: str = "") -> str:
        return "".join(self._pascal_case(part) for part in parts) + suffix

    def _safe_identifier(self, value: str) -> str:
        candidate = value.replace("-", "_")
        candidate = "".join(
            character if character.isalnum() or character == "_" else "_"
            for character in candidate
        )
        if not candidate:
            candidate = "field_"
        if candidate[0].isdigit():
            candidate = f"field_{candidate}"
        if iskeyword(candidate):
            candidate = f"{candidate}_"
        return candidate

    def _pascal_case(self, value: str) -> str:
        pieces = [piece for piece in self._safe_identifier(value).split("_") if piece]
        if not pieces:
            return "Field"
        return "".join(piece[:1].upper() + piece[1:] for piece in pieces)

    def _enum_member_name(self, value: Any) -> str:
        if isinstance(value, str):
            candidate = self._safe_identifier(value).upper()
        else:
            candidate = self._safe_identifier(str(value)).upper()
        if not candidate:
            candidate = "VALUE"
        return candidate


def generate_classes(
    database_or_config: Any,
    output_path: str | Path,
    *,
    cli_binary: str = "mergeway-cli",
) -> Path:
    """Generate a Python module of dataclasses from a Mergeway schema."""

    if hasattr(database_or_config, "list_entities") and hasattr(
        database_or_config, "entity_schema"
    ):
        database = database_or_config
    else:
        from .database import Database

        database = Database(database_or_config, cli_binary=cli_binary)

    generator = ModelGenerator(database)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generator.render(), encoding="utf-8")
    return output
