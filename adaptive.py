"""Approved T14/T15 rules. Database aliases: beginner=easy, advanced=hard."""
from statistics import mean, median

from psycopg.types.json import Jsonb

LEGACY_VERSION = 'rules-v1'
ORDERED_VERSION = 'rules-v2-ordered-control'
VERSION = 'rules-v3-pair-exclusion'
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
    """Predetermined IDs; never query learner history or performance."""
    pools = {level: conn.execute(
        "SELECT scenario_id, matched_pair_id FROM training_scenarios WHERE difficulty_level=%s ORDER BY scenario_id",
        (level,)).fetchall() for level in LEVELS}
    selected = choose_schedule(pools, CONTROL_SCHEDULE)
    if selected is None:
        raise ControlScheduleUnavailable()
    return selected


def next_scenario(training_session, reviewed):
    ids = training_session['scenario_ids'] or []
    return next((sid for sid in ids if sid not in reviewed), None)


def sequence_enforced(training_session):
    # New protocol only: never reinterpret historic v1 sessions.
    return training_session['algorithm_version'] in (ORDERED_VERSION, VERSION)


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
    if training_session['algorithm_version'] not in (LEGACY_VERSION, ORDERED_VERSION, VERSION):
        return None  # Historical sessions are never retroactively adapted.
    sid = training_session['session_id']
    rows = conn.execute('''SELECT * FROM training_responses
        WHERE session_id = %s ORDER BY response_id''', (sid,)).fetchall()
    fixed_control = (training_session['algorithm_version'] in (ORDERED_VERSION, VERSION)
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
        available = select_scenarios(conn, training_session['user_id'], proposed,
                                     max(remaining, 1), reviewed,
                                     pair_exclusion=training_session['algorithm_version'] == VERSION)
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
