---
title: "mergeway-python Getting Started"
linkTitle: "Python SDK"
description: "Extend your Mergeway database with functionality in Python"
weight: 30
cascade:
  type: docs
---

This guide shows how to use `mergeway-python` with an existing Mergeway
repository. It covers:

- generating Python models from `mergeway.yaml`
- connecting to the repository from Python
- basic CRUD operations
- common repository-level operations

## Prerequisites

You need:

- a Python environment with `mergeway-python` installed
- `mergeway-cli` available on `PATH`
- an existing Mergeway repository with a `mergeway.yaml` file

## 1. Generate Python Models

You can generate Python classes for an existing repository with the package CLI.

If you know the repository root:

```bash
mergeway-python generate \
  --root /path/to/mergeway-repo \
  /path/to/mergeway-repo/generated_models.py
```

If you want to point directly at the config file:

```bash
mergeway-python generate \
  --config /path/to/mergeway-repo/mergeway.yaml \
  /path/to/mergeway-repo/generated_models.py
```

This writes a Python module containing:

- one dataclass per Mergeway entity
- nested dataclasses for object fields
- enums for native Mergeway enum fields
- an `ENTITY_REGISTRY` used by the runtime

## 2. Connect to a Repository

Once you have generated models, create a `Database` instance and point it at
the repository config.

```python
from pathlib import Path

from mergeway import Database

repo_root = Path("/path/to/mergeway-repo")

db = Database(
    repo_root / "mergeway.yaml",
    classes_module=repo_root / "generated_models.py",
)
```

If you do not pass `classes_module`, the wrapper still works, but reads return
plain dictionaries instead of typed objects.

## 3. Read Data

### Get one object

```python
post = db.get("Post", "post-001")
print(post.title)
print(post.to_payload())
```

### List all objects of one entity

```python
users = db.list("User")
for user in users:
    print(user.id, user.email)
```

### Export repository data

```python
all_data = db.export()
print(all_data.keys())

posts = db.export("Post")
for post in posts:
    print(post.id, post.status)
```

## 4. Create Objects

You can create objects with generated model classes.

```python
User = db.classes_module.User

created = db.create(
    User,
    User(
        id="user-cara",
        name="Cara Example",
        email="cara@example.com",
        roles=["author"],
    ),
)

print(created.id)
print(created.name)
```

You can also create objects from plain dictionaries:

```python
db.create(
    "User",
    {
        "id": "user-dan",
        "name": "Dan Example",
        "email": "dan@example.com",
        "roles": ["editor"],
    },
)
```

## 5. Update Objects

Replace the stored object:

```python
updated = db.update(
    "User",
    "user-cara",
    {
        "id": "user-cara",
        "name": "Cara Updated",
        "email": "cara@example.com",
        "roles": ["author", "editor"],
    },
)

print(updated.name)
print(updated.roles)
```

Or merge fields into the existing object:

```python
db.update(
    "User",
    "user-cara",
    {"roles": ["author", "editor", "reviewer"]},
    merge=True,
)
```

## 6. Delete Objects

```python
message = db.delete("User", "user-cara")
print(message)
```

## 7. Repository Operations

### Validate the repository

```python
result = db.validate()
print(result)
```

You can also run specific validation phases:

```python
db.validate(phases=["schema", "references"])
```

### Format repository files

Rewrite files in place:

```python
db.format(in_place=True)
```

Check whether formatting is already clean:

```python
db.format(lint=True, in_place=False)
```

### Export repository data

```python
snapshot = db.export()
print(snapshot["User"])
```

## 8. Generate Models Programmatically

You can generate the model file from Python instead of the CLI:

```python
repo_root = Path("/path/to/mergeway-repo")
db = Database(repo_root / "mergeway.yaml")

generated_path = db.generate_classes(repo_root / "generated_models.py")
print(generated_path)
```

After generation, the `Database` instance loads the generated module
automatically, so future reads return typed objects.

## 9. Minimal End-to-End Script

```python
from pathlib import Path

from mergeway import Database

repo_root = Path("/path/to/mergeway-repo")

db = Database(repo_root / "mergeway.yaml")
db.generate_classes(repo_root / "generated_models.py")

User = db.classes_module.User

created = db.create(
    User,
    User(
        id="user-cara",
        name="Cara Example",
        email="cara@example.com",
        roles=["author"],
    ),
)

loaded = db.get("User", "user-cara")
updated = db.update(
    "User",
    "user-cara",
    {
        "id": "user-cara",
        "name": "Cara Updated",
        "email": "cara@example.com",
        "roles": ["author", "editor"],
    },
)

db.validate()
db.format(in_place=True)
db.delete("User", "user-cara")

print(created.to_payload())
print(loaded.to_payload())
print(updated.to_payload())
```

