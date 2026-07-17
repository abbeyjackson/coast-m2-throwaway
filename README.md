# coast-m1-throwaway

Throwaway repository driven end-to-end by the **Coast M1 walking skeleton**
(F7/D58). Safe to delete at any time.

Read the history of `main` to watch one tiny feature travel the whole
pipeline without a human reading code: plan proposed → plan merged → tests
fail → tests green → reviewed merge, every merge behind a green
deterministic gate.

- `plans/<feature>/` — the plan, ticket, and proof files (the audit record)
- `Scripts/checks/verify_proof.py` — the deterministic CI gate
- `.github/workflows/coast-gates.yml` — the gates that must be green
