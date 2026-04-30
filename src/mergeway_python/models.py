"""Shared model helpers for generated Mergeway entity classes."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from types import UnionType
from typing import Any, ClassVar, Mapping, Union, get_args, get_origin, get_type_hints


def serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, GeneratedModel):
        return value.to_payload()
    if isinstance(value, list):
        return [serialize_value(item) for item in value]
    return value


def _deserialize_value(value: Any, annotation: Any) -> Any:
    if value is None:
        return None
    if annotation is Any:
        return value

    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        last_error: Exception | None = None
        for candidate in get_args(annotation):
            if candidate is type(None):
                continue
            try:
                return _deserialize_value(value, candidate)
            except (TypeError, ValueError) as error:
                last_error = error
        if last_error is not None:
            raise last_error
        return value

    if origin is list:
        if not isinstance(value, list):
            raise TypeError(f"Expected list value, got {type(value).__name__}")
        item_type = get_args(annotation)[0] if get_args(annotation) else Any
        return [_deserialize_value(item, item_type) for item in value]

    if annotation is str:
        if not isinstance(value, str):
            raise TypeError(f"Expected string value, got {type(value).__name__}")
        return value
    if annotation is int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"Expected integer value, got {type(value).__name__}")
        return value
    if annotation is float:
        if not isinstance(value, int | float) or isinstance(value, bool):
            raise TypeError(f"Expected number value, got {type(value).__name__}")
        return float(value)
    if annotation is bool:
        if not isinstance(value, bool):
            raise TypeError(f"Expected boolean value, got {type(value).__name__}")
        return value
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return annotation(value)
    if isinstance(annotation, type) and is_dataclass(annotation):
        if not isinstance(value, Mapping):
            raise TypeError(f"Expected object value, got {type(value).__name__}")
        return annotation.from_payload(value)
    return value


class GeneratedModel:
    """Base class for generated Mergeway entity and nested object models."""

    __mergeway_entity_name__: ClassVar[str]
    __mergeway_field_aliases__: ClassVar[dict[str, str]] = {}

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "GeneratedModel":
        """Build a model instance from a Mergeway JSON payload."""

        type_hints = get_type_hints(cls, include_extras=True)
        aliases = getattr(cls, "__mergeway_field_aliases__", {})
        kwargs: dict[str, Any] = {}

        for model_field in fields(cls):
            payload_key = aliases.get(model_field.name, model_field.name)
            if payload_key not in payload:
                continue
            annotation = type_hints.get(model_field.name, Any)
            kwargs[model_field.name] = _deserialize_value(
                payload[payload_key], annotation
            )
        return cls(**kwargs)

    def to_payload(self) -> dict[str, Any]:
        """Serialize a model instance to a Mergeway JSON payload."""

        aliases = getattr(type(self), "__mergeway_field_aliases__", {})
        payload: dict[str, Any] = {}

        for model_field in fields(self):
            value = getattr(self, model_field.name)
            if value is None:
                continue
            payload_key = aliases.get(model_field.name, model_field.name)
            payload[payload_key] = serialize_value(value)
        return payload
