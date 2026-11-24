# Security policy

## Supported versions

Security fixes are made against the latest version on the default branch. There are no separate long-term-support branches at this stage.

## Reporting a vulnerability

Please do not publish exploitable vulnerability details in a public issue. Use GitHub's **Report a vulnerability** / private vulnerability reporting feature for this repository when available. If that feature is unavailable, contact the repository owner privately through GitHub and request a secure channel before sharing technical details.

Include the affected version or commit, impact, reproduction steps, and any mitigations you know. Please allow maintainers a reasonable opportunity to investigate and prepare a fix before public disclosure.

## Deployment note

GGUFBox is intended for local or trusted-network use. Before exposing an instance beyond localhost, set a strong `GGUFBOX_API_KEY` and place the service behind properly configured HTTPS and network access controls. Do not assume the optional API key is a substitute for a complete multi-user authentication or authorization system.
