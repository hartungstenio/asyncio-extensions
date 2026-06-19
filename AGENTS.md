# AGENTS.md

Guidelines for AI agents working on this repository.

## Project overview

`asyncio-extensions` is a typed Python library (3.11+) with utility functions and classes for `asyncio`. It is published to PyPI and built with [Hatch](https://hatch.pypa.io).

## Architecture

All implementation lives under `src/asyncio_extensions/`. Every submodule is **private** (prefixed with `_`). The public API is re-exported exclusively from `__init__.py` — do not import private modules in user-facing documentation or examples.

| Module | Theme |
|---|---|
| `_compat.py` | Version compatibility shims (Python 3.11–3.15). No new features here. |
| `_sync.py` | Bridging sync and async code. |
| `_scheduling.py` | Event-loop control utilities. |
| `_iterators.py` | Async iteration utilities. |
| `_task_groups.py` | TaskGroup extensions. |

When creating a new module, add a row to this table describing its theme.

When adding a new public symbol, define it in the appropriate private module and add a re-export to `__init__.py` using the `from .module import name as name` pattern (the `as name` alias is required to mark it as explicitly re-exported for type checkers).

## Commands

```bash
# Run tests (current Python)
hatch run pytest

# Run tests across all supported versions
hatch test

# Lint and auto-fix
hatch fmt

# Check lint without fixing
hatch fmt --check

# Type checking
hatch run mypy src/asyncio_extensions
```

All of the above must pass before committing.

## Tests

Test files live in `tests/` and are named `test_<module>.py` to match the private module they cover (e.g. `tests/test_sync.py` covers `_sync.py`). Tests import directly from the private module under test, not from the top-level package — except for symbols from other modules used as helpers, which are imported from the package.

```python
# correct
from asyncio_extensions._sync import asyncify
from asyncio_extensions import checkpoint  # helper from another module
```

Maintain the same order as the source module: tests for each symbol should appear in the order the symbols are defined, and within a symbol's tests, individual cases should follow the order of branches and conditions in the implementation.

The test suite runs against Python 3.11, 3.12, 3.13, 3.14 and 3.15 in CI. When writing version-specific tests, use `@pytest.mark.skipif(sys.version_info < (3, X), ...)`.

## Compatibility

`_compat.py` centralises version guards. Prefer adding backports and shims there and importing from `_compat` in the consuming module, keeping `if sys.version_info >= ...` blocks out of the other modules when possible.

## Code style

- Linter: **ruff** with an extensive ruleset (see `pyproject.toml`). Run `hatch fmt` before committing.
- Docstrings: **PEP 257** (enforced via `ruff --select D` with `convention = "pep257"`). Use imperative mood for the summary line. Document constructor arguments in the class docstring, not in `__init__`.
- Type annotations are required on all public symbols. The package ships a `py.typed` marker.

## Commits and changelog

Commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/) — this is enforced by a `commitizen` pre-commit hook.

```
feat(scope): short description
fix(scope): short description
refactor(scope): short description
docs: short description
```

When adding or changing user-visible behaviour, add an entry to the `[UNRELEASED]` section of `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format (`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`).
