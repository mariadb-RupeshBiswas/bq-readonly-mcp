# Publishing

Release runbook for maintainers.

---

## Prerequisites

1. **PyPI account** with an API token for the `bq-readonly-mcp` project.
2. A **`pypi` GitHub environment** configured on the repository with the secret `PYPI__TOKEN__` set to the API token.
3. The `main` branch must be **protected** (PR-only, CI must pass, 1 approving review).

The publish workflow runs automatically on every push to `main`. It is
idempotent: if the version is already on PyPI, the workflow skips the upload
step instead of failing.

---

## Release steps

### 1. Bump the version

Edit `pyproject.toml`:

```toml
[project]
version = "0.2.0"   # was 0.1.0
```

Follow [Semantic Versioning](https://semver.org/):

- **Patch** (`0.1.x`) — bug fixes, documentation fixes, dependency updates.
- **Minor** (`0.x.0`) — new features, backward-compatible.
- **Major** (`x.0.0`) — breaking changes.

### 2. Update CHANGELOG.md

Add a new entry at the top of `CHANGELOG.md`:

```markdown
## [0.2.0] — YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Fixed
- ...
```

### 3. Open a PR

Include both the version bump and the CHANGELOG entry in the same PR.
The PR title should follow conventional commits, e.g. `chore: release 0.2.0`.

### 4. Merge after CI is green and reviewed

CI (ruff, mypy, pytest) must pass. One approving review is required.
Merge using a squash or merge commit — either is fine.

### 5. Publish workflow runs automatically

After the merge, the `Publish` workflow starts within seconds.
It will:
1. Build the wheel and sdist.
2. Check whether this version is already on PyPI (idempotent guard).
3. If missing: publish to PyPI using `UV_PUBLISH_TOKEN`.
4. If already present with matching hashes: skip (no-op).
5. If present with mismatched hashes: fail loudly (bump the version first).

### 6. Verify on PyPI

Within ~3 minutes of the workflow completing:

```bash
# Check the PyPI page
open https://pypi.org/project/bq-readonly-mcp/

# Smoke test
uvx bq-readonly-mcp@0.2.0 --help
```

---

## Rollback

PyPI does not allow deleting or replacing published files. If a bad release
goes out:

1. Fix the bug.
2. Bump to the next patch version (e.g., `0.2.1`).
3. Follow the release steps above.

The bad version will remain on PyPI but will not be installed by default once
a newer version exists (pip and uv install the latest by default).

---

## Manual publish (emergency only)

If the GitHub Actions workflow is unavailable, you can publish manually:

```bash
uv sync
uv build --no-create-gitignore
UV_PUBLISH_TOKEN=<your-token> uv publish --check-url https://pypi.org/simple/
```

Only do this from a clean checkout of the version tag.
