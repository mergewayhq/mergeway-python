# Contributing

## Development Setup

This project uses `devenv` for the development shell and `uv` for Python
environment syncing.

```bash
devenv shell
UV_CACHE_DIR=.cache/uv uv sync
```

## Running Tests

Run the full test suite in the synced environment:

```bash
UV_CACHE_DIR=.cache/uv uv run python -m unittest
```

You can also run the non-CLI tests with the plain interpreter:

```bash
python -m unittest
```

## Notes

- `mergeway-cli` is provided by the `devenv` shell.
- The end-to-end test fixture is local to this repository under `tests/fixtures/full`.
