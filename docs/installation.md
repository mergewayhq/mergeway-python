---
title: "Install mergeway-python"
linkTitle: "Installation"
description: "Install mergeway-python with uv"
weight: 20
---

`mergeway-python` requires `mergeway-cli` to be available on `PATH`.

If you have not installed the CLI yet, [follow the official guide first](https://mergewayhq.github.io/cli/getting-started/installation/)!

## Install with `uv`

If you are adding `mergeway-python` to a project, install the published package
with:

```bash
uv add mergeway
```

If you are working from a local checkout and want an editable install, run:

```bash
uv sync
```

After installation, continue to the [getting started guide](mergeway-python-getting-started.md).
