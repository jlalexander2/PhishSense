# Eight-scenario advanced-pool feasibility (proposed, not imported)

The three approved-for-import matched pairs contribute at most one scenario each.
The two independent drafts contribute one scenario each. Thus the maximum valid
advanced block is 3 + 1 + 1 = **5 distinct scenarios**.

Exhaustive enumeration of all 56 five-scenario subsets found **8 valid subsets**
(one of two members from each pair, plus both independent scenarios). These are
subsets, not presentation orders. Every valid five-scenario block must include
both new independent scenarios. There is no spare independent capacity.

With the existing five intermediate baseline scenarios, this supports a ten-email
experimental session that advances to hard at the first five-response boundary.
The control schedule can select two advanced scenarios provided they are not
members of the same pair. This is an inventory feasibility check, not proof that
the application already enforces pair exclusions: that implementation remains
pending, as does approval of these two drafts and import of the advanced pool.

If any independent item is unavailable or unsuitable, a five-hard block is no
longer feasible with this pool. The existing repeat-across-sessions policy is not
changed here. No class balance rule, schedule or threshold was changed. Across
valid five-hard blocks, phishing counts can range from one to four; no stricter
balance requirement was assumed.

The original six scenarios and approved JSONL are unchanged. No database access,
scenario import, participant update or historical-results modification occurred.
