# Supabase migration validation

Validation date: November 8, 2026.

The authoritative SQLite source was `phishsense.db`. The earlier backups contain
matching account data; `phishsense_backup_2.db` also contains matching scenarios,
but neither backup contains the latest sessions or responses.

| Table | SQLite source | Supabase after migration and testing |
|---|---:|---:|
| users | 1 | 1 |
| training_scenarios | 19 | 19 |
| training_sessions | 3 | 4 (3 migrated, 1 additional live session) |
| training_responses | 6 | 6 |

The approved PostgreSQL schema was created in `public`. Copying preserved original
IDs, password hashes, scenario fields, timestamps, written reasoning, confidence,
response times, classifications, and difficulty/session status. Every copied field
was compared before committing. Identity counters were restarted above existing
IDs. Timezone-free SQLite timestamps were interpreted as UTC. No source integrity
or foreign-key violations were found; post-migration orphan checks returned zero.
All four application tables have row-level security enabled.

Initial copy attempts rolled back because the session pooler returned floating
point values with insufficient text precision (`extra_float_digits=0`). The shared
connection now explicitly sets UTC and `extra_float_digits=3` after connecting,
because startup options were not sufficient for this endpoint. The final copy
passed exact field comparisons and committed successfully. A regression test
checks that double precision values round-trip exactly.

All **10 automated tests passed against Supabase**, including configuration/TLS
checks, real PostgreSQL constraints and transaction rollback, synthetic SQLite
migration, import validation/idempotency, registration/duplicate registration,
password verification, login/logout, protected routes, the ten-email Evercrest
inbox, training submissions, reasoning, confidence, educational feedback, progress,
completion, invalid submissions, and replay rejection. Integration tests used
synthetic records in unique temporary schemas, which were removed afterward.
A final read-only check found one additional public training session beyond the
three migrated records. It was left unchanged; no public records were deleted
to restore the source count. Other public table counts match the source.

TLS remains `verify-full` with the locally configured trusted Supabase CA.
No credentials, password hashes, account details, or learner answers are included
in this report. Existing uncommitted work and datasets were preserved. No Git
commit or push was performed.

## Preservation and limits

SHA-256 checks confirmed all three original SQLite files were unchanged after
migration. Keep these files as local backups; do not commit them.

The source contains three unfinished sessions and six responses, with no completed
sessions. These records were retained. Inbox scenario selections live in signed
Flask browser sessions, not database rows; an unavailable browser session cannot
be reconstructed from the old database alone.

The real account's password hash was preserved exactly. Automated login tests use
synthetic credentials; a manual browser login with the original account password
remains a useful final user check. No password reset was performed. Browser visual
checks were not part of the automated Flask test-client validation.

Restart Flask to load the latest connection configuration, then log in at
`http://127.0.0.1:5000/login`. Existing accounts should retain their original passwords.
