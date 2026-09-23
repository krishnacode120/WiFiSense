# Contributing

Keep changes focused, preserve explicit authorization on every connection path, and
never introduce password discovery or plaintext credential storage.

1. Create a branch from main.
2. Add regression tests for behavior changes using mocked adapters.
3. Run pytest, npm run build, and the browser workflow where UI behavior changed.
4. Format frontend files with npm run format.
5. Stage only source/docs/synthetic fixtures and run python scripts/check_repository.py.
6. Open a pull request explaining the behavior and verification performed.

A hardware validation report should include OS/driver versions and the scenario but
must exclude real passwords, tokens, private SSIDs/BSSIDs, and personal history.
Future schema changes should include an explicit migration.
