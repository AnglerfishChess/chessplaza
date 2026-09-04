---
name: complete-checkpoint
description: Run after completing significant work — implementing a feature, fixing a bug, refactoring, or any substantial code changes. Proactively ensure code quality before reporting work as done.
---

# Complete Checkpoint

After finishing a significant piece of work, run these checks:

## 1. Lint and Format

```bash
uvx ruff check --fix . && uvx ruff format .
```

## 2. Type-check

```bash
uvx pyrefly check
```

## 3. Run Tests

```bash
uv run --no-sync pytest
```

The `llm`-marked tests need a live Claude session and are excluded by default;
run them with `uv run --no-sync pytest -m llm`.

## One-Liner

```bash
uvx ruff check --fix . && uvx ruff format . && uvx pyrefly check && uv run --no-sync pytest
```

## Behavior

1. Run the checks without asking permission
2. If everything passes: briefly report success, continue with summary
3. If anything fails: fix the issues, then re-run checks
4. Don't report work as "done" until checks pass
