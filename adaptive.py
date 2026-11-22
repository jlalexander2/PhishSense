"""Approved T14/T15 rules. Database aliases: beginner=easy, advanced=hard."""
from statistics import mean, median

from psycopg.types.json import Jsonb

LEGACY_VERSION = 'rules-v1'
ORDERED_VERSION = 'rules-v2-ordered-control'
PAIR_VERSION = 'rules-v3-pair-exclusion'
VERSION = 'rules-v4-balanced-selection'
PAIR_VERSIONS = (PAIR_VERSION, VERSION)
CONTROL_SCHEDULE = ('intermediate',) * 5 + (
    'beginner', 'advanced', 'intermediate', 'beginner', 'advanced')
LEVELS = ('beginner', 'intermediate', 'advanced')
BLOCK_SIZE = 5


class ControlScheduleUnavailable(Exception):
    """Required approved scenario inventory is incomplete."""


def choose_schedule(candidates, schedule, blocked_pairs=()):
    """Search a fixed difficulty schedule without repeating IDs or pair keys.

    Candidate order defines preference (performance-independent for controls).
    Backtracking avoids rejecting a feasible schedule after a greedy pair choice.
    """
    def search(position, selected, used_ids, used_pairs):
        if position == len(schedule):
            return selected
        for row in candidates[schedule[position]]:
            sid, pair = row['scenario_id'], row['matched_pair_id']
            if sid in used_ids or (pair and pair in used_pairs):
                continue
            result = search(position + 1, selected + [sid], used_ids | {sid},
                            used_pairs | ({pair} if pair else set()))
            if result is not None:
                return result
        return None
    # Capacity checks also prevent factorial searches for undersized pools.
    for level in set(schedule):
        groups = {('pair', r['matched_pair_id']) if r['matched_pair_id'] else
                  ('id', r['scenario_id']) for r in candidates[level]
                  if not r['matched_pair_id'] or r['matched_pair_id'] not in blocked_pairs}
        if len(groups) < schedule.count(level):
            return None
    return search(0, [], set(), set(blocked_pairs))


def control_scenarios(conn):
    """Historical v2/v3 inventory helper; v4 uses balanced_session_scenarios."""
    pools = {level: conn.execute(
        "SELECT scenario_id, matched_pair_id FROM training_scenarios WHERE difficulty_level=%s ORDER BY scenario_id",
        (level,)).fetchall() for level in LEVELS}
    selected = choose_schedule(pools, CONTROL_SCHEDULE)
    if selected is None:
        raise ControlScheduleUnavailable()
    return selected



def balanced_candidates(conn, user_id=None):
    """Controls use only inventory/ID order; adaptive novelty is a soft preference."""
    if user_id is None:
        rows = conn.execute("SELECT scenario_id, matched_pair_id, is_phishing, difficulty_level "
                            "FROM training_scenarios ORDER BY scenario_id").fetchall()
    else:
        rows = conn.execute("""
            SELECT s.scenario_id, s.matched_pair_id, s.is_phishing, s.difficulty_level
            FROM training_scenarios s LEFT JOIN (
                SELECT r.scenario_id, MAX(r.answered_at) AS last_completed
                FROM training_responses r JOIN training_sessions ts ON ts.session_id=r.session_id
                WHERE ts.user_id=%s GROUP BY r.scenario_id
            ) history ON history.scenario_id=s.scenario_id
            ORDER BY history.last_completed ASC NULLS FIRST, RANDOM()
        """, (user_id,)).fetchall()
    return {level: [r for r in rows if r['difficulty_level'] == level] for level in LEVELS}


def choose_balanced_schedule(candidates, schedule, prefix=(), require_branches=False):
    """Research-only quotas: 2/3 baseline, 3/2 remainder, ten distinct pair-safe IDs.

    Prefix is immutable already-presented rows, not learner answer labels.
    Memoized search preserves candidate preference among feasible complete plans.
    """
    from functools import lru_cache
    schedule = tuple(schedule)
    prefix = tuple(prefix)
    if len(schedule) != 10 or len(prefix) > 10:
        return None
    initial_ids = tuple(r['scenario_id'] for r in prefix)
    initial_pairs = [r['matched_pair_id'] for r in prefix if r['matched_pair_id']]
    if (len(set(initial_ids)) != len(initial_ids) or len(set(initial_pairs)) != len(initial_pairs)
            or any(r['difficulty_level'] != schedule[i] for i,r in enumerate(prefix))):
        return None

    @lru_cache(None)
    def search(position, used_ids, used_pairs, phishing, baseline_count):
        if phishing > 5 or phishing + 10-position < 5:
            return None
        if position <= 5 and (baseline_count > 2 or baseline_count + 5-position < 2):
            return None
        if position == 10:
            return () if phishing == 5 and baseline_count == 2 else None
        available = []
        for level in set(schedule[position:]):
            pool = [r for r in candidates[level] if r['scenario_id'] not in used_ids
                    and (not r['matched_pair_id'] or r['matched_pair_id'] not in used_pairs)]
            if len({('pair',r['matched_pair_id']) if r['matched_pair_id'] else ('id',r['scenario_id'])
                    for r in pool}) < schedule[position:].count(level):
                return None
            available.extend(pool)
        if (sum(r['is_phishing'] for r in available) < 5-phishing or
                sum(1-r['is_phishing'] for r in available) < 5-(position-phishing)):
            return None
        for row in candidates[schedule[position]]:
            sid, pair = row['scenario_id'], row['matched_pair_id']
            if sid in used_ids or (pair and pair in used_pairs):
                continue
            tail = search(position+1, used_ids | {sid}, used_pairs | ({pair} if pair else set()),
                          phishing+row['is_phishing'], baseline_count+(row['is_phishing'] if position<5 else 0))
            if tail is not None:
                return (sid,) + tail
        return None

    # Select a feasible baseline before reserving the rest of an experimental plan.
    # With current pools only advanced rows are paired, but check generically.
    if require_branches:
        from itertools import combinations
        for baseline in combinations(candidates['intermediate'], 5):
            if sum(r['is_phishing'] for r in baseline) != 2:
                continue
            if all(choose_balanced_schedule(candidates, ('intermediate',)*5+(level,)*5,
                                           baseline) is not None for level in LEVELS):
                plan = choose_balanced_schedule(candidates, schedule, baseline)
                if plan is not None:
                    return plan
        return None
    tail = search(len(prefix), frozenset(initial_ids), frozenset(initial_pairs),
                  sum(r['is_phishing'] for r in prefix),
                  sum(r['is_phishing'] for r in prefix[:5]))
    return list(initial_ids+tail) if tail is not None else None


def balanced_session_scenarios(conn, user_id, group):
    pools = balanced_candidates(conn, None if group == 'control' else user_id)
    if not any(pools.values()):
        return []
    schedule = CONTROL_SCHEDULE if group == 'control' else ('intermediate',)*10
    plan = choose_balanced_schedule(pools, schedule, require_branches=group == 'experimental')
    if plan is None:
        raise ControlScheduleUnavailable()
    return plan


def balanced_plan_safe(conn, ids):
    if len(ids) != 10 or not pair_safe(conn, ids):
        return False
    rows = {r['scenario_id']:r for r in conn.execute(
        'SELECT scenario_id,is_phishing,difficulty_level FROM training_scenarios WHERE scenario_id=ANY(%s::integer[])',
        (list(ids),))}
    return (len(rows) == 10 and sum(rows[i]['is_phishing'] for i in ids) == 5
            and sum(rows[i]['is_phishing'] for i in ids[:5]) == 2
            and all(rows[i]['difficulty_level'] == 'intermediate' for i in ids[:5]))


def next_scenario(training_session, reviewed):
    ids = training_session['scenario_ids'] or []
    return next((sid for sid in ids if sid not in reviewed), None)


def sequence_enforced(training_session):
    # New protocol only: never reinterpret historic v1 sessions.
    return training_session['algorithm_version'] in (ORDERED_VERSION, PAIR_VERSION, VERSION)


def evaluate_difficulty(current, responses, group):
    """Pure evaluator; only a complete five-response block may affect difficulty."""
    if current not in LEVELS:
        raise ValueError('Unknown difficulty')
    if group != 'experimental':
        return current, 'non_adaptive'
    if len(responses) != BLOCK_SIZE:
        return current, 'incomplete_block'
    accuracy = mean(r['is_correct'] for r in responses)
    seconds = median(r['response_time'] for r in responses)
    confidence = mean(r['confidence_level'] for r in responses)
    step, reason = 0, 'maintain'
    if accuracy >= .8 and seconds <= 60 and confidence >= 4:
        step, reason = 1, 'strong_performance'
    elif accuracy < .6:
        step, reason = -1, 'low_accuracy'
    elif accuracy == .6 and seconds > 90 and confidence <= 2:
        step, reason = -1, 'accuracy_time_confidence'
    target = LEVELS[max(0, min(2, LEVELS.index(current) + step))]
    return target, 'level_boundary' if step and target == current else reason


def select_scenarios(conn, user_id, difficulty, limit, exclude=(), pair_exclusion=True):
    """Prefer never-completed scenarios; reuse oldest completions only as needed.

    Every scenario occurs at most once in an inbox. Unanswered reservations do
    not count as completed; excluded IDs protect already reviewed inbox rows.
    """
    if limit <= 0:
        return []
    exclude = list(exclude)
    rows = conn.execute('''
        SELECT s.scenario_id, s.matched_pair_id
        FROM training_scenarios s
        LEFT JOIN (
            SELECT r.scenario_id, MAX(r.answered_at) AS last_completed
            FROM training_responses r
            JOIN training_sessions ts ON ts.session_id = r.session_id
            WHERE ts.user_id = %s
            GROUP BY r.scenario_id
        ) history ON history.scenario_id = s.scenario_id
        WHERE s.difficulty_level = %s
          AND (%s OR s.introduced_in_version IS NULL)
          AND NOT (s.scenario_id = ANY(%s::integer[]))
        ORDER BY history.last_completed ASC NULLS FIRST, RANDOM()
    ''', (user_id, difficulty, pair_exclusion, list(exclude))).fetchall()
    if not pair_exclusion:
        return [r['scenario_id'] for r in rows[:limit]]
    blocked = {r['matched_pair_id'] for r in conn.execute(
        'SELECT matched_pair_id FROM training_scenarios WHERE scenario_id=ANY(%s::integer[])',
        (list(exclude),)) if r['matched_pair_id']}
    # Preserve history ordering while returning at most one representative per pair.
    selected = []
    for row in rows:
        pair = row['matched_pair_id']
        if pair and pair in blocked:
            continue
        selected.append(row['scenario_id'])
        if pair:
            blocked.add(pair)
        if len(selected) == limit:
            break
    return selected



def pair_safe(conn, ids):
    pairs = [r['matched_pair_id'] for r in conn.execute(
        'SELECT matched_pair_id FROM training_scenarios WHERE scenario_id=ANY(%s::integer[])',
        (list(ids),)) if r['matched_pair_id']]
    return len(pairs) == len(set(pairs)) and len(ids) == len(set(ids))


def evaluate_session(conn, training_session):
    """Called under a session row lock, in the same transaction as the response."""
    if training_session['algorithm_version'] not in (LEGACY_VERSION, ORDERED_VERSION, PAIR_VERSION, VERSION):
        return None  # Historical sessions are never retroactively adapted.
    sid = training_session['session_id']
    rows = conn.execute('''SELECT * FROM training_responses
        WHERE session_id = %s ORDER BY response_id''', (sid,)).fetchall()
    fixed_control = (training_session['algorithm_version'] in (ORDERED_VERSION, PAIR_VERSION, VERSION)
                     and training_session['study_group'] == 'control')
    scheduled_level = training_session['current_difficulty']
    if fixed_control:
        following = next_scenario(training_session, {r['scenario_id'] for r in rows})
        if following is not None:
            scheduled_level = conn.execute('SELECT difficulty_level FROM training_scenarios WHERE scenario_id=%s',
                                           (following,)).fetchone()['difficulty_level']
        conn.execute('UPDATE training_sessions SET current_difficulty=%s WHERE session_id=%s',
                     (scheduled_level, sid))
    if not rows or len(rows) % BLOCK_SIZE:
        return None
    block_number = len(rows) // BLOCK_SIZE
    if conn.execute('''SELECT 1 FROM difficulty_evaluations
        WHERE session_id=%s AND block_number=%s''', (sid, block_number)).fetchone():
        return None
    block = rows[-BLOCK_SIZE:]
    current = training_session['current_difficulty']
    if fixed_control:
        proposed, reason = scheduled_level, 'fixed_control_schedule'
    elif any(r['difficulty_at_response'] != current for r in block):
        proposed, reason = current, 'mixed_difficulty_block'
    else:
        proposed, reason = evaluate_difficulty(current, block, training_session['study_group'])
    applied = proposed
    reviewed = {r['scenario_id'] for r in rows}
    ids = training_session['scenario_ids']
    completed = [i for i in ids if i in reviewed]
    remaining = len(ids) - len(completed)
    if proposed != current and not fixed_control:
        # Check availability even at session completion; never claim promotion to
        # a difficulty that has no approved scenarios.
        if training_session['algorithm_version'] == VERSION and remaining:
            pools = balanced_candidates(conn, training_session['user_id'])
            lookup = {r['scenario_id']:r for pool in pools.values() for r in pool}
            prefix = [lookup[i] for i in completed]
            plan = choose_balanced_schedule(pools,
                tuple(r['difficulty_at_response'] for r in rows) + (proposed,)*remaining, prefix)
            available = plan[len(completed):] if plan is not None else []
        else:
            # At response ten there is no remaining classification quota. Preserve
            # the prior evaluator's one-item difficulty availability semantics.
            available = select_scenarios(conn, training_session['user_id'], proposed,
                                         max(remaining, 1), reviewed,
                                         pair_exclusion=training_session['algorithm_version'] in PAIR_VERSIONS)
        if len(available) < max(remaining, 1):
            applied = current
            reason = 'target_scenarios_unavailable'
        elif remaining:
            ids = completed + available[:remaining]
    conn.execute('''INSERT INTO difficulty_evaluations (
        session_id, block_number, response_ids, algorithm_version, study_group,
        previous_difficulty, proposed_difficulty, applied_difficulty,
        accuracy, median_response_time, mean_confidence, reason)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', (
        sid, block_number, [r['response_id'] for r in block], training_session['algorithm_version'],
        training_session['study_group'], current, proposed, applied,
        mean(r['is_correct'] for r in block), median(r['response_time'] for r in block),
        mean(r['confidence_level'] for r in block), reason))
    conn.execute('''UPDATE training_sessions SET current_difficulty=%s, scenario_ids=%s
        WHERE session_id=%s''', (applied, Jsonb(ids), sid))
    return ids
