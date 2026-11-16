"""Learner-owned session results; calculated from recorded outcomes, never rewritten."""
from collections import Counter
from statistics import mean

from mistakes import summarize_mistakes

LEVELS = ('beginner', 'intermediate', 'advanced')


def measurements(responses):
    count = len(responses)
    confidence = Counter(r['confidence_level'] for r in responses)
    return dict(
        response_count=count,
        correct_count=sum(r['is_correct'] for r in responses),
        accuracy_percent=100 * sum(r['is_correct'] for r in responses) / count if count else None,
        average_response_time=mean(r['response_time'] for r in responses) if count else None,
        average_confidence=mean(r['confidence_level'] for r in responses) if count else None,
        confidence_distribution=[dict(level=i, count=confidence[i]) for i in range(1, 6)],
    )


def difficulty_measurements(responses):
    return [dict(level=level, **measurements([
        r for r in responses if r['difficulty_at_response'] == level])) for level in LEVELS]


def summarize_session(training_session, responses):
    """Keep actual presented difficulty and stored correctness, including legacy data."""
    ordered = sorted(responses, key=lambda r: r['response_id'])
    result = dict(training_session)
    result.update(measurements(ordered))
    result['is_complete'] = training_session['completed_at'] is not None
    result['by_difficulty'] = difficulty_measurements(ordered)
    result['responses'] = [dict(r, position=i + 1,
        expected_answer=r['user_answer'] if r['is_correct'] else 1-r['user_answer'])
        for i, r in enumerate(ordered)]
    result['mistakes'] = summarize_mistakes(ordered)
    # Descriptive associations only; no diagnosis or adaptive-rule changes.
    result['practice_areas'] = [e for e in result['mistakes']['errors'] if e['count']]
    return result


def historical_performance(summaries):
    completed = sorted((s for s in summaries if s['is_complete']),
                       key=lambda s: (s['completed_at'], s['session_id']))
    measurable = [s for s in completed if s['response_count']]
    all_responses = [r for s in completed for r in s['responses']]
    result = dict(completed_sessions=completed, completed_count=len(completed),
                  in_progress=[s for s in summaries if not s['is_complete']],
                  overall=measurements(all_responses),
                  by_difficulty=difficulty_measurements(all_responses),
                  average_session_accuracy=mean(s['accuracy_percent'] for s in measurable) if measurable else None,
                  accuracy_change_points=None)
    if len(measurable) >= 2:
        result['accuracy_change_points'] = measurable[-1]['accuracy_percent']-measurable[-2]['accuracy_percent']
    return result


RESPONSE_QUERY = '''SELECT r.*, s.subject, s.phishing_technique, s.learning_objectives
    FROM training_responses r
    JOIN training_sessions ts ON ts.session_id=r.session_id
    JOIN training_scenarios s ON s.scenario_id=r.scenario_id
    WHERE ts.user_id=%s AND ts.session_type='training' '''


def session_results(conn, user_id, session_id):
    training = conn.execute('''SELECT * FROM training_sessions
        WHERE session_id=%s AND user_id=%s AND session_type='training' ''',
        (session_id, user_id)).fetchone()
    if training is None:
        return None
    rows = conn.execute(RESPONSE_QUERY+' AND r.session_id=%s ORDER BY r.response_id',
                        (user_id, session_id)).fetchall()
    return summarize_session(training, rows)


def learner_history(conn, user_id):
    sessions = conn.execute('''SELECT * FROM training_sessions
        WHERE user_id=%s AND session_type='training' ORDER BY started_at, session_id''',
        (user_id,)).fetchall()
    responses = conn.execute(RESPONSE_QUERY+' ORDER BY r.response_id', (user_id,)).fetchall()
    grouped = {s['session_id']: [] for s in sessions}
    for row in responses:
        grouped[row['session_id']].append(row)
    return historical_performance([summarize_session(s, grouped[s['session_id']]) for s in sessions])


def complete_training_session(conn, user_id, session_id, fallback_ids=()):
    """Idempotently finalize exactly the planned ten emails, in the save transaction.

    No backfills or read-triggered writes. Caller commits with the tenth response.
    """
    training = conn.execute('''SELECT * FROM training_sessions
        WHERE session_id=%s AND user_id=%s AND session_type='training' FOR UPDATE''',
        (session_id, user_id)).fetchone()
    if training is None:
        return False
    if training['completed_at'] is not None:
        return True
    expected = training['scenario_ids'] if training['scenario_ids'] is not None else list(fallback_ids)
    if len(expected) != 10 or len(set(expected)) != 10:
        return False
    rows = conn.execute('SELECT scenario_id FROM training_responses WHERE session_id=%s',
                        (session_id,)).fetchall()
    if len(rows) != 10 or {r['scenario_id'] for r in rows} != set(expected):
        return False
    conn.execute('''UPDATE training_sessions SET completed_at=CURRENT_TIMESTAMP
        WHERE session_id=%s AND user_id=%s AND completed_at IS NULL''', (session_id, user_id))
    return True
