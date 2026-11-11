# Milestone 4 testing

Install the application requirements and configure credentials locally using
`.env.example`. The example contains placeholders only; actual environment files,
certificates, databases and local recording credentials are not committed.

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

The full suite contains **52 tests**. Without TEST_DATABASE_URL, database tests
explicitly skip; those skips do not demonstrate successful Supabase validation.
Set TEST_DATABASE_URL locally to a disposable Supabase development database or an
authorized test target. TLS uses verify-full and the configured trusted CA.

Database fixtures create unique phishsense_test_* schemas and synthetic records,
then remove their schemas. They do not use real accounts or public training
records. Test login passwords and Flask signing keys are generated at runtime,
not published reusable credentials. Do not point a schema-creation test role at
an unapproved database.

Coverage includes registration/login, password hashes, PostgreSQL constraints and
rollback, read-only SQLite migration, scenario import validation/idempotency,
ordered ten-email workflows, feedback, reasoning/confidence/timing/progress,
adaptive threshold boundaries, fixed control scheduling, matched-pair exclusion,
hard-pool capacity, legacy protocol protection, recurring errors, exact metadata
associations, learner isolation and read-only summary access.

Browser validation completed high/low experimental and high/low control profiles
and verified the new mistake summary. Local browser launchers and recordings
are intentionally kept outside the submission because they contain demo login
information or machine-specific setup. These are optional and are not required
by pytest or the production application.

For release validation, run the complete suite once with the real PostgreSQL test
target, record failures/skips honestly, compare public application-table hashes
before/after, and verify temporary-schema cleanup. Stop on a connection failure;
do not weaken certificate verification or repeatedly retry. Historical pooler
refusals were intermittent; successful runs showed no connection leaks or backend
saturation, but their original cause was not conclusively established.

## Milestone 4 submission validation — November 10, 2026

The complete suite passed **52 tests, 0 failures, 0 skips** against Supabase in
149.68 seconds after replacing fixed test login secrets with runtime-generated
values. All five public application-table hashes remained unchanged. The run
reported zero connection failures and zero test connections left open. Previously
verified Chrome workflows cover both groups and the read-only mistake summary.
No production imports, migrations, group assignments or server restarts were
performed to prepare this submission.
