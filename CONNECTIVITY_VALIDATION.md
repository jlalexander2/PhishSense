# Post-import connectivity investigation and validation

The authorized migration and eight-record import were preserved. Neither was
repeated. Flask was not restarted. No application code, credentials, TLS settings,
endpoint, pooler configuration, group assignments or production records were
changed during this investigation.

## Endpoint and DNS

The configured host is a Supabase shared-pooler hostname and uses session-mode
port 5432. No explicit hostaddr override is configured. DNS resolved three unique
addresses. Each was checked once with its resolved address while retaining the
configured hostname for TLS identity verification; all three passed certificate
verification, authentication and a read-only SELECT 1. No addresses, connection
strings, passwords or secret keys are recorded here.

These checks establish current reachability. The earlier connection refusals did
not recur during this investigation; their exact historical cause could not be
established without the contemporaneous network/pooler logs. They must not be
reported as a proven DNS problem, connection leak or exhausted database.

## Limits and connection lifecycle

PostgreSQL reported max_connections=60. Before the suite, five client backends
were observed: one active and four idle. During the complete test suite, a
read-only observer sampled aggregate activity every two seconds:

- 70 observations; peak seven PostgreSQL client backends, peak two active.
- 518 successful real test-client connections opened sequentially.
- Sampled peak of one open test-client connection; zero remained open afterward.
- Zero observed connection failures and zero observer errors.

The application opens and closes short-lived connections for requests, and the
test fixture creates/drops isolated schemas using context-managed connections.
This creates connection churn, but the measured run showed neither a leak nor
backend saturation. Two-second sampling cannot exclude brief between-sample
spikes or explain the historical outage. The shared pooler's separate client and
pool-size limits are not exposed by the SQL statistics used here; PostgreSQL's
60-connection limit must not be presented as that front-end limit.

Supabase distinguishes client connections from backend connections:
https://supabase.com/docs/guides/database/connecting-to-postgres/pooling-and-limits

## Isolated failure investigation and complete suite

The formerly failed test,
`test_sequence_enforcement_and_inbox[experimental]`, passed independently
(1 passed). The old traceback was not retained, so its original exact cause
cannot be established retrospectively. No functional failure reproduced.

The complete post-import suite then passed: **43 passed in 139.68 seconds**.
It ran once with stop-on-first-failure enabled. Coverage includes ordered
baseline completion, approved threshold decisions, promotion to five distinct
pair-compatible hard items, fixed non-adaptive control scheduling under
contrasting performance, server-side order/pair checks, and legacy session
protection. All integration records were synthetic and isolated from public.

## Data and cleanup verification

Hashes and counts for users, training_scenarios, training_sessions,
training_responses and difficulty_evaluations matched exactly before and after
testing and after scratch-schema cleanup. Existing historical records were not
modified. Every imported field, including context, explanation, objectives,
pair key and introduction version, matched the approved eight-record package.

| Difficulty | Phishing | Legitimate | Total |
|---|---:|---:|---:|
| Easy | 4 | 3 | 7 |
| Intermediate | 5 | 7 | 12 |
| Advanced | 4 | 4 | 8 |
| Total | 13 | 14 | 27 |

All three two-member matched pairs and both independent advanced items were
verified. Live read-only selection produced five compatible hard items and the
approved ten-email control schedule. The advanced pool still has no spare
independent capacity and should be expanded/piloted before participant research.

Two orphaned generated test schemas remained from interrupted runs: one empty,
one containing only expected test tables and synthetic addresses. No external
foreign-key references were found. Cleanup used explicit table drops followed
by DROP SCHEMA RESTRICT, without CASCADE, in one transaction; public-table hashes
were rechecked before commit. Remaining temporary test schemas: **zero**.

## Remaining limitation

Post-import validation is now successful, but recurring endpoint refusal is not
proven permanently resolved. If it returns, stop the run and capture the time,
DNS-address outcomes and pooler/client graphs or provider logs before retrying.
No automatic retry loop or unverified TLS workaround was introduced.
