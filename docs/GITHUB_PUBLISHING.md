# GitHub publishing checklist

This source tree is prepared for a public GitHub repository. No repository has been created or pushed by this document; the owner should confirm the account/organization, repository name, and public visibility before publishing.

## Recommended repository metadata

- **Repository name:** `ggufbox` (use this if available)
- **Visibility:** Public for broad discovery, after the owner confirms
- **Description:** `Self-hosted GGUF inference server with a bilingual web UI, OpenAI-compatible API, and vision support.`
- **Topics:** `gguf`, `llama-cpp`, `local-ai`, `self-hosted`, `fastapi`, `openai-compatible`, `vision`, `large-language-models`
- **Default branch:** `main`
- **Website:** leave blank until there is a stable project site; do not use a temporary development URL
- **README landing page:** `README.md` (English first, with a prominent link to `README.ar.md`)

After the first push, enable Issues and Discussions, ensure the CI workflow is required or at least visible on pull requests, and configure a social preview image if one is prepared. Add a short GitHub release note when a version is formally released; do not tag a release just because the source has been prepared.

## Model and repository hygiene

The `.gitignore` intentionally excludes `models/*.gguf`, local databases, uploads, `.env` secrets, and virtual environments. It explicitly keeps `models/SOURCE.md` and the empty directory marker. Do not add model binaries to Git or Git LFS by default: users can fetch the official demo pair from the upstream Hugging Face repository using the command in either README. The upstream SmolVLM weights are Apache-2.0; the GGUFBox application code is MIT. Keep those licenses clearly distinguished.

Before a push, verify the staged set with `git status --short`, `git diff --cached --stat`, and `git diff --cached --check`. Confirm no `.env`, database, uploads, `.gguf`, access token, or personal data is staged. Run the CI-equivalent test command from `CONTRIBUTING.md`.

## Publish only after owner confirmation

Once the GitHub connector is enabled and the owner has selected the namespace and confirmed public visibility, create/push the initial repository from the project directory using the authorized GitHub CLI. Substitute the confirmed owner or organization; do not guess it:

```bash
gh repo create OWNER/ggufbox --public --source=. --remote=origin --push
```

If `ggufbox` is unavailable, choose a short distinctive repository name and update the repository metadata before pushing. Add the actual repository URL to README badges and `pyproject.toml` only after the owner/URL is known. Public visibility is a deliberate release decision, not an automatic result of local preparation.
