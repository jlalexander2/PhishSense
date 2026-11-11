"""Read-only recurring classification mistakes; independent of adaptive decisions."""
from collections import Counter

RECURRENCE_THRESHOLD = 2
ERROR_LABELS = {'missed_phishing': 'Missed phishing', 'false_alarm': 'False alarms'}


def summarize_mistakes(rows):
    counts = Counter()
    associations = Counter()
    seen = set()
    for row in rows:
        # One response is one occurrence, even if its metadata repeats an objective.
        if row['response_id'] in seen:
            continue
        seen.add(row['response_id'])
        if row['is_correct'] != 0:
            continue
        # With binary answers, stored incorrectness + the submitted answer
        # identifies the error without reinterpreting a historical scenario label.
        error = 'missed_phishing' if row['user_answer'] == 0 else 'false_alarm'
        counts[error] += 1
        technique = row.get('phishing_technique')
        if isinstance(technique, str) and technique.strip():
            associations[(error, 'Phishing technique', technique)] += 1
        objectives = row.get('learning_objectives')
        if isinstance(objectives, list):
            for objective in {v for v in objectives if isinstance(v, str) and v.strip()}:
                associations[(error, 'Learning objective', objective)] += 1
    return {
        'threshold': RECURRENCE_THRESHOLD,
        'errors': [dict(error_type=key, label=label, count=counts[key],
                        recurring=counts[key] >= RECURRENCE_THRESHOLD)
                   for key, label in ERROR_LABELS.items()],
        'associations': [dict(error_type=error, label=ERROR_LABELS[error],
                              metadata_type=kind, concept=concept, count=count,
                              recurring=count >= RECURRENCE_THRESHOLD)
                         for (error, kind, concept), count in sorted(associations.items())],
    }


def learner_mistakes(conn, user_id):
    rows = conn.execute('''
        SELECT r.response_id, r.user_answer, r.is_correct,
               s.phishing_technique, s.learning_objectives
        FROM training_responses r
        JOIN training_sessions ts ON ts.session_id = r.session_id
        JOIN training_scenarios s ON s.scenario_id = r.scenario_id
        WHERE ts.user_id = %s AND ts.session_type = 'training'
        ORDER BY r.response_id
    ''', (user_id,)).fetchall()
    return summarize_mistakes(rows)
