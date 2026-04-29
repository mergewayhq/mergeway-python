from __future__ import annotations

import importlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

from .codegen import generate_classes as render_classes
from .models import GeneratedModel, serialize_value

try:
    from plumbum import local
    from plumbum.commands.processes import ProcessExecutionError
except (
    ModuleNotFoundError
):  # pragma: no cover - exercised only in environments missing the dependency
    local = None
    ProcessExecutionError = RuntimeError


class MergewayCLIError(RuntimeError):
    def __init__(
        self, message: str, *, command: list[str], stdout: str = "", stderr: str = ""
    ):
        super().__init__(message)
        self.command = command
        self.stdout = stdout
        self.stderr = stderr


class Database:
    def __init__(
        self,
        config_path: str | Path,
        *,
        classes_module: ModuleType | str | Path | None = None,
        cli_binary: str = "mergeway-cli",
    ) -> None:
        self.config_path = Path(config_path).resolve()
        self.root = self.config_path.parent
        self.cli_binary = cli_binary
        self.classes_module = self._load_classes_module(classes_module)

    def list_entities(self) -> list[str]:
        stdout = self._run("entity", "list", output_format="json")
        return [line.strip() for line in stdout.splitlines() if line.strip()]

    def entity_schema(self, entity: str) -> dict[str, Any]:
        return self._run_json("entity", "show", entity)

    def get(self, entity: str | type[GeneratedModel], object_id: str) -> Any:
        entity_name = self._entity_name(entity)
        payload = self._run_json("get", object_id, "--type", entity_name)
        return self._cast_one(entity_name, payload)

    def list(self, entity: str | type[GeneratedModel]) -> list[Any]:
        entity_name = self._entity_name(entity)
        exported = self.export(entity_name)
        return exported if isinstance(exported, list) else exported.get(entity_name, [])

    def create(
        self,
        entity: str | type[GeneratedModel],
        payload: GeneratedModel | Mapping[str, Any],
        *,
        object_id: str | None = None,
    ) -> Any:
        entity_name = self._entity_name(entity)
        normalized_payload = self._normalize_payload(payload)
        self._run_with_payload(
            ["create", "--type", entity_name],
            normalized_payload,
            object_id=object_id,
        )
        resolved_id = object_id or self._identifier_from_payload(
            entity_name, normalized_payload
        )
        if resolved_id is None:
            return None
        return self.get(entity_name, resolved_id)

    def update(
        self,
        entity: str | type[GeneratedModel],
        object_id: str,
        payload: GeneratedModel | Mapping[str, Any],
        *,
        merge: bool = False,
    ) -> Any:
        entity_name = self._entity_name(entity)
        normalized_payload = self._normalize_payload(payload)
        args = ["update", "--type", entity_name, "--id", object_id]
        if merge:
            args.append("--merge")
        self._run_with_payload(args, normalized_payload)
        return self.get(entity_name, object_id)

    def delete(self, entity: str | type[GeneratedModel], object_id: str) -> str:
        entity_name = self._entity_name(entity)
        return self._run("delete", object_id, "--type", entity_name, yes=True).strip()

    def validate(self, *, phases: list[str] | None = None) -> str:
        args: list[str] = ["validate"]
        for phase in phases or []:
            args.extend(["--phase", phase])
        return self._run(*args).strip()

    def format(
        self,
        *paths: str | Path,
        in_place: bool = True,
        lint: bool = False,
        stdout: bool = False,
    ) -> str:
        args: list[str] = ["fmt", *[str(path) for path in paths]]
        if stdout:
            args.append("--stdout")
        elif in_place and not lint:
            args.append("--in-place")
        if lint:
            args.append("--lint")
        return self._run(*args)

    def export(self, *entities: str | type[GeneratedModel]) -> Any:
        entity_names = [self._entity_name(entity) for entity in entities]
        payload = self._run_json("export", *entity_names)
        if not entity_names:
            return {
                name: self._cast_many(name, objects)
                for name, objects in payload.items()
            }
        if len(entity_names) == 1:
            entity_name = entity_names[0]
            return self._cast_many(entity_name, payload.get(entity_name, []))
        return {
            entity_name: self._cast_many(entity_name, payload.get(entity_name, []))
            for entity_name in entity_names
        }

    def generate_classes(self, output_path: str | Path) -> Path:
        rendered_path = render_classes(self, output_path)
        self.classes_module = self._load_classes_module(rendered_path)
        return rendered_path

    def _run_with_payload(
        self,
        args: list[str],
        payload: Mapping[str, Any],
        *,
        object_id: str | None = None,
    ) -> str:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as handle:
            json.dump(payload, handle)
            temp_path = Path(handle.name)
        try:
            command = list(args)
            if object_id is not None:
                command.extend(["--id", object_id])
            command.extend(["--file", str(temp_path)])
            return self._run(*command, output_format="json")
        finally:
            temp_path.unlink(missing_ok=True)

    def _run(
        self, *args: str, output_format: str | None = None, yes: bool = False
    ) -> str:
        if local is None:
            raise RuntimeError("plumbum is required to use Database")

        command_args = [
            "--root",
            str(self.root),
            "--config",
            str(self.config_path),
        ]
        if output_format is not None:
            command_args.extend(["--format", output_format])
        if yes:
            command_args.append("--yes")
        command_args.extend(str(arg) for arg in args)

        command = local[self.cli_binary][command_args]
        try:
            _, stdout, _ = command.run()
            return stdout
        except ProcessExecutionError as error:
            stdout = getattr(error, "stdout", "") or ""
            stderr = getattr(error, "stderr", "") or ""
            message = stderr.strip() or stdout.strip() or str(error)
            raise MergewayCLIError(
                message,
                command=[self.cli_binary, *command_args],
                stdout=stdout,
                stderr=stderr,
            ) from error

    def _run_json(self, *args: str) -> Any:
        stdout = self._run(*args, output_format="json")
        if not stdout.strip():
            return None
        return json.loads(stdout)

    def _entity_name(self, entity: str | type[GeneratedModel]) -> str:
        if isinstance(entity, str):
            return entity
        return getattr(entity, "__mergeway_entity_name__", entity.__name__)

    def _normalize_payload(
        self, payload: GeneratedModel | Mapping[str, Any]
    ) -> dict[str, Any]:
        if isinstance(payload, GeneratedModel):
            return payload.to_payload()
        if not isinstance(payload, Mapping):
            raise TypeError("payload must be a mapping or generated model")
        return {str(key): serialize_value(value) for key, value in payload.items()}

    def _identifier_from_payload(
        self, entity_name: str, payload: Mapping[str, Any]
    ) -> str | None:
        identifier = self.entity_schema(entity_name).get("Identifier") or {}
        field_name = identifier.get("Field")
        if not field_name:
            return None
        value = payload.get(field_name)
        return None if value is None else str(value)

    def _cast_many(
        self, entity_name: str, payloads: list[Mapping[str, Any]]
    ) -> list[Any]:
        return [self._cast_one(entity_name, payload) for payload in payloads]

    def _cast_one(self, entity_name: str, payload: Mapping[str, Any]) -> Any:
        model = self._resolve_model(entity_name)
        if model is None:
            return dict(payload)
        return model.from_payload(payload)

    def _resolve_model(self, entity_name: str) -> type[GeneratedModel] | None:
        if self.classes_module is None:
            return None
        registry = getattr(self.classes_module, "ENTITY_REGISTRY", {})
        model = registry.get(entity_name) if isinstance(registry, dict) else None
        if model is not None:
            return model
        candidate = getattr(self.classes_module, entity_name, None)
        if isinstance(candidate, type) and issubclass(candidate, GeneratedModel):
            return candidate
        return None

    def _load_classes_module(
        self,
        module_ref: ModuleType | str | Path | None,
    ) -> ModuleType | None:
        if module_ref is None:
            return None
        if isinstance(module_ref, ModuleType):
            return module_ref

        path = Path(module_ref)
        if path.exists():
            return self._load_module_from_path(path)
        return importlib.import_module(str(module_ref))

    def _load_module_from_path(self, path: Path) -> ModuleType:
        resolved = path.resolve()
        module_name = f"mergeway_python_generated_{abs(hash(resolved))}"
        spec = importlib.util.spec_from_file_location(module_name, resolved)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load generated module from {resolved}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
