"""Explicit draft-only loading for isolated, empty disposable review schemas."""
import hashlib
import json
import os
from pathlib import Path
import re

from psycopg import sql
from psycopg.conninfo import make_conninfo
from psycopg.types.json import Jsonb
from validation_support import supabase_project

ROOT=Path(__file__).resolve().parent
PROTECTED=('source_id','is_phishing','difficulty_level','matched_pair_id','learning_objectives')
PRESENTATION=('sender_name','sender_email','subject','email_body','training_context','explanation','phishing_intent','phishing_technique','presentation_metadata')


def load_review():
    raw=(ROOT/'data/scenarios_approved_for_prototype.jsonl').read_bytes()
    document=json.loads((ROOT/'data/scenario_realism_drafts.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=document['base_dataset_sha256']:
        raise ValueError('Approved base has changed; draft review is required.')
    approved={s['source_id']:s for s in map(json.loads,raw.decode().splitlines())}
    revisions={}
    for item in document['scenarios']:
        original=approved[item['source_id']];proposed=item['proposed']
        digest=hashlib.sha256(json.dumps(original,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        if digest!=item['base_sha256'] or any(proposed.get(k)!=original.get(k) for k in PROTECTED):
            raise ValueError('Review revision changes protected research metadata.')
        if proposed['review_status']!='draft' or not proposed.get('training_context'):
            raise ValueError('Review requires explicit draft status and visible context.')
        if proposed['source_id'] in revisions:
            raise ValueError('Duplicate review scenario.')
        revisions[proposed['source_id']]=item
    if set(revisions)!=set(approved):
        raise ValueError('Review inventory must match the complete approved base.')
    return revisions


def seed_review(conn, original_rows):
    """Insert presentation revisions only into an empty, verified TEST schema.

    No historical records are copied or updated. Caller owns transaction/commit.
    """
    test_url=os.environ.get('TEST_DATABASE_URL')
    if not test_url:
        raise ValueError('Explicit TEST_DATABASE_URL required.')
    actual=make_conninfo(host=conn.info.host,user=conn.info.user,port=conn.info.port,dbname=conn.info.dbname)
    if supabase_project(actual)!=supabase_project(test_url) or not conn.pgconn.ssl_in_use:
        raise ValueError('Authenticated review connection is not the verified test target.')
    namespace=conn.execute('SELECT current_schema() AS name').fetchone()['name']
    if not re.fullmatch(r'phishsense_(?:test|review)_[0-9a-f]{32}',namespace or ''):
        raise ValueError('Review requires a generated isolated schema, never public.')
    for table in ('users','training_sessions','training_responses','difficulty_evaluations','training_scenarios'):
        if conn.execute(sql.SQL('SELECT count(*) AS n FROM {}.{}').format(sql.Identifier(namespace),sql.Identifier(table))).fetchone()['n']:
            raise ValueError('Refusing to change a nonempty review target.')
    revisions=load_review()
    if len(original_rows)!=len(revisions) or {s['source_id'] for s in original_rows}!=set(revisions):
        raise ValueError('Source scenario inventory differs; review required.')
    for row in original_rows:
        proposed=revisions[row['source_id']]['proposed']
        if any(row.get(k)!=proposed.get(k) for k in PROTECTED):
            raise ValueError('Database research metadata differs from reviewed base.')
    # Optional evidence is local to empty review/test copies. No production DDL.
    conn.execute(sql.SQL('ALTER TABLE {}.training_scenarios ADD COLUMN IF NOT EXISTS presentation_metadata JSONB').format(sql.Identifier(namespace)))
    for row in original_rows:
        values=dict(row)
        values.update({k:revisions[row['source_id']]['proposed'].get(k) for k in PRESENTATION})
        columns=list(values)
        args=[Jsonb(values[k]) if k in ('learning_objectives','presentation_metadata') and values[k] is not None else values[k] for k in columns]
        conn.execute(sql.SQL('INSERT INTO {}.training_scenarios ({}) VALUES ({})').format(
            sql.Identifier(namespace),sql.SQL(',').join(map(sql.Identifier,columns)),sql.SQL(',').join(sql.Placeholder() for k in columns)),args)
    conn.execute(sql.SQL("SELECT setval(pg_get_serial_sequence(%s,'scenario_id'),(SELECT max(scenario_id) FROM {}.training_scenarios))").format(sql.Identifier(namespace)),(namespace+'.training_scenarios',))
    return len(original_rows)
