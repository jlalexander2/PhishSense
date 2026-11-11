"""Approved additive metadata migration and eight-scenario import, atomically."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from psycopg import sql
from adaptive import VERSION, CONTROL_SCHEDULE, control_scenarios, pair_safe, select_scenarios
from database import get_db_connection
from import_scenarios import import_scenarios, validate_scenarios

TABLES = ('users', 'training_scenarios', 'training_sessions', 'training_responses', 'difficulty_evaluations')
CONTENT = ('sender_name','sender_email','subject','email_body','is_phishing','difficulty_level',
           'explanation','phishing_intent','phishing_technique','target_category','source_id',
           'training_context','learning_objectives','matched_pair_id','introduced_in_version')


def verified_package():
    manifest = json.loads((ROOT/'data/advanced_approval_manifest.json').read_text())
    drafts = []
    for name, digest in manifest['source_sha256'].items():
        path = ROOT/'data'/name
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Reviewed source changed')
        drafts.extend(json.loads(path.read_text()))
    approved = json.loads((ROOT/'data/evercrest_advanced_approved.json').read_text())
    if len(approved) != 8 or validate_scenarios(approved):
        raise ValueError('Invalid approved package')
    for original, copy in zip(drafts, approved):
        if any(original[k] != copy.get(k) for k in original if k not in
               ('review_status','review_notes','matched_pair_id')):
            raise ValueError('Approved content differs from reviewed content')
    expected_pairs = ('evercrest-consent','evercrest-audit','evercrest-enrollment')
    for i, row in enumerate(approved):
        expected = expected_pairs[i % 3] if i < 6 else None
        if row['matched_pair_id'] != expected or row['introduced_in_version'] != VERSION:
            raise ValueError('Invalid pair/version mapping')
    lines = (ROOT/'data/scenarios_approved_for_prototype.jsonl').read_bytes().splitlines(keepends=True)
    if hashlib.sha256(b''.join(lines[:-8])).hexdigest() != manifest['original_approved_jsonl_sha256']:
        raise ValueError('Existing approved dataset changed')
    if [json.loads(line) for line in lines[-8:]] != approved:
        raise ValueError('Approved dataset/package mismatch')
    return approved


def integrate():
    approved = verified_package()
    with get_db_connection() as conn:
        conn.execute('SET LOCAL search_path TO public')
        conn.execute("SET LOCAL lock_timeout = '5s'")
        conn.execute(sql.SQL('LOCK TABLE {} IN ACCESS EXCLUSIVE MODE').format(
            sql.SQL(', ').join(map(sql.Identifier, TABLES))))
        snapshots = {}
        for table in TABLES:
            rows = conn.execute(sql.SQL('SELECT * FROM {} ORDER BY 1').format(sql.Identifier(table))).fetchall()
            columns = [r['column_name'] for r in conn.execute('''SELECT column_name FROM information_schema.columns
                WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position''', (table,))]
            snapshots[table] = columns, rows
        fields = {'training_context','learning_objectives','matched_pair_id','introduced_in_version'}
        present = fields.intersection(snapshots['training_scenarios'][0])
        if present and present != fields:
            raise ValueError('Partial metadata migration; manual review required')
        if not present:
            conn.execute((ROOT/'migrations/005_scenario_metadata.sql').read_text())
        result = import_scenarios(approved, connection=conn)
        for row in approved:
            found = conn.execute('SELECT * FROM training_scenarios WHERE source_id=%s', (row['source_id'],)).fetchall()
            if len(found) != 1 or any(found[0][field] != row.get(field) for field in CONTENT):
                raise ValueError('Imported field verification failed; no overwrite attempted')
        hard = select_scenarios(conn, 0, 'advanced', 5)
        control = control_scenarios(conn)
        if len(hard) != 5 or not pair_safe(conn, hard) or len(control) != 10 or not pair_safe(conn, control):
            raise ValueError('Pair-safe inventory cannot support approved schedules')
        levels = {r['scenario_id']:r['difficulty_level'] for r in conn.execute('SELECT scenario_id,difficulty_level FROM training_scenarios')}
        if tuple(levels[i] for i in control) != CONTROL_SCHEDULE:
            raise ValueError('Control schedule mismatch')
        for table,(columns,before) in snapshots.items():
            query = sql.SQL('SELECT {} FROM {}').format(sql.SQL(', ').join(map(sql.Identifier, columns)),sql.Identifier(table))
            args = ()
            if table == 'training_scenarios':
                query += sql.SQL(' WHERE scenario_id=ANY(%s::integer[])')
                args = ([r['scenario_id'] for r in before],)
            query += sql.SQL(' ORDER BY 1')
            if conn.execute(query,args).fetchall() != before:
                raise ValueError('Existing-record preservation check failed')
            print(table + ': original records unchanged; count=' + str(len(before)))
    print('Committed: metadata, eight approved scenarios, and pair-safe inventory verified.')
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    try:
        if args.apply:
            integrate()
        else:
            verified_package()
            print('Reviewed package verified. Preview only; no database connection or changes.')
    except Exception as error:
        print('Integration stopped; database transaction rolled back if opened. Error type:',type(error).__name__)
        print('Details withheld to protect credentials and research data.')
        raise SystemExit(1)
