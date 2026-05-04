# mergeway-python

`mergeway-python` is a Python automation layer for Mergeway repositories. The
published PyPI package is [`mergeway`](https://pypi.org/project/mergeway/). It
wraps `mergeway-cli`, uses the CLI's JSON output as its data boundary, and can
generate typed Python models from a repository's `mergeway.yaml` schema.
For the broader Mergeway toolset, see the main website:
<https://mergewayhq.github.io/>

## Goals

- provide a Python-first API for Mergeway repository automation
- keep `mergeway-cli` as the source of truth for reads, writes, and validation
- generate typed dataclasses from Mergeway entity definitions
- expose repository operations without introducing a custom persistence layer

## Installation

`mergeway-python` requires `mergeway-cli` to be available on `PATH`.

Install the package into your Python environment:

```bash
pip install mergeway
```

If you are working from a local checkout and want an editable install:

```bash
pip install -e .
```

If `mergeway-cli` is not already available in your environment, install it by
following the official installation guide:
<https://mergewayhq.github.io/cli/getting-started/installation/>

## Quick Example

This example assumes you already have a Mergeway repository on disk:

```python
from pathlib import Path

from mergeway import Database

repo_root = Path("/path/to/mergeway-repo")
db = Database(repo_root / "mergeway.yaml")

db.generate_classes(repo_root / "generated_models.py")

user = db.get("User", "user-alice")
posts = db.export("Post")

print(user.to_payload())
print([post.title for post in posts])
```

## Full Docs

- [Getting started](docs/mergeway-python-getting-started.md)

## Contributing
Please see [CONTRIBUTING.md](./CONTRIBUTING.md)
