# mergeway-python

`mergeway-python` is a Python automation layer for Mergeway repositories. It
wraps `mergeway-cli`, uses the CLI's JSON output as its data boundary, and can
generate typed Python models from a repository's `mergeway.yaml` schema.

## Goals

- provide a Python-first API for Mergeway repository automation
- keep `mergeway-cli` as the source of truth for reads, writes, and validation
- generate typed dataclasses from Mergeway entity definitions
- expose repository operations without introducing a custom persistence layer

## Installation

`mergeway-python` requires `mergeway-cli` to be available on `PATH`.

Install the package into your Python environment:

```bash
pip install .
```

If you are installing from a local checkout and want editable installs while
using the package:

```bash
pip install -e .
```

If `mergeway-cli` is not already available in your environment, install it
using the distribution method you use for Mergeway in your organization.

## Quick Example

This example is copy-paste runnable from a checkout of this repository after
syncing the environment:

```bash
UV_CACHE_DIR=.cache/uv uv run python - <<'PY'
from pathlib import Path

from mergeway import Database

repo_root = Path("tests/fixtures/full")
db = Database(repo_root / "mergeway.yaml")

db.generate_classes(repo_root / "generated_models.py")

user = db.get("User", "user-alice")
posts = db.export("Post")

print(user.to_payload())
print([post.title for post in posts])
PY
```

## Full Docs

- [Product documentation](.local/docs/product.md)
- [Tech stack documentation](.local/docs/tech-stack.md)
- [Contributing guide](CONTRIBUTING.md)
