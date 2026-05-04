---
title: "mergeway-python"
linkTitle: "Python SDK"
description: "Python automation for Mergeway repositories"
weight: 10
cascade:
  type: docs
---

`mergeway-python` is a Python automation layer for Mergeway repositories. The
published PyPI package is [`mergeway`](https://pypi.org/project/mergeway/).
It wraps `mergeway-cli`, uses the CLI's JSON output as its data boundary, and
can generate typed Python models from a repository's `mergeway.yaml` schema.

Use `mergeway-python` when you want to:

- read repository data from Python
- create, update, and delete objects with a Python API
- validate or format a repository from Python
- generate typed dataclasses from your Mergeway schema

To install the package and prepare your environment, continue to the
[installation guide](installation.md).
