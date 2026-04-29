# mergeway-python

`mergeway-python` is a Python automation layer for Mergeway repositories.

It shells out to `mergeway-cli` with `plumbum`, uses the CLI's JSON output for
repository reads and writes, and can generate typed dataclasses from a
repository's `mergeway.yaml` schema.
