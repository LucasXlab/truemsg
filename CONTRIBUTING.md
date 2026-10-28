# Contributing

Use a source checkout with Python 3.11+ and Git 2.31+. Run `make dev`, then `make check` and `make build`. Tests use disposable synthetic Git repositories and no API keys. The only runtime dependency is Rich; developer tools are declared in the `dev` extra.

Add a reproducible Git fixture for each parsing or CLI change. Preserve the distinction between observable Git facts, limited lexical hints and semantic judgments. Never claim a rule proves a commit is truthful. Test failures, malformed configuration and incomplete input must fail clearly, not turn into PASS.

Keep changes small, include regression tests, and avoid new network or model dependencies. Do not add real repository diffs, personal identities, tokens, machines paths or business data to fixtures, screenshots or demos. Existing valid MIT notices must remain.

Hook integration is optional. Never overwrite a user's existing hook or disable a rule just to make tests green. No package-registry publication, remote CI result or ownership of an unverified namespace is implied by this source checkout.
