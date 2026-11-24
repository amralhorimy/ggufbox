# Contributing to GGUFBox

Thanks for helping improve GGUFBox. Contributions, bug reports, documentation fixes, and carefully scoped feature proposals are welcome.

## Before opening a pull request

1. Search existing issues and pull requests so work is not duplicated.
2. For a substantial change, open an issue or discussion first to agree on the scope.
3. Keep changes focused and update the English and Arabic documentation when user-visible behavior changes.
4. Do not commit model weights, `.env` files, databases, uploads, or other local user data. The repository intentionally keeps large GGUF binaries out of Git.

## Development and tests

Use Python 3.11 or 3.12 and a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
GGUFBOX_ENGINE=mock python -m pytest -q
python -m compileall -q app tests
```

The mock engine lets the test suite run without downloading model weights or compiling `llama-cpp-python`. If a change affects real inference, vision, Docker, or model loading, include the environment and reproduction steps in the pull request; avoid making CI depend on multi-gigabyte model downloads.

## Pull requests

Describe the user problem, the approach, and any trade-offs. Include tests run, screenshots for UI changes, and any migration or configuration notes. Keep secrets and personal conversation data out of screenshots and logs. Maintainers may request changes before merging.

By submitting a contribution, you agree that it may be distributed under the repository's MIT license. You retain copyright in your contributions; the license grants the permissions stated in `LICENSE`.
