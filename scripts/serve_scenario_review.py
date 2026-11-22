"""Serve draft emails and synthetic workflows ONLY in a separate disposable project.

No production imports or history copies. Stop the server to remove its own schema.
"""
import json
import hashlib
import argparse
import logging
from pathlib import Path
import secrets
import sys
import uuid
from unittest.mock import patch
import os

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from database import get_db_connection
from validation_support import require_test_target
from scenario_review import load_review,seed_review
from psycopg import sql
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=5007)
    parser.add_argument('--final',action='store_true',help='Use separate final-pass credential/state artifacts.')
    args=parser.parse_args()
    test_url=require_test_target()
    # Explicit read-only scenario source; never read/copy participant accounts/history.
    with get_db_connection() as c:
        c.execute('SET TRANSACTION READ ONLY')
        originals=c.execute('SELECT * FROM public.training_scenarios ORDER BY scenario_id').fetchall()
    def connect():
        with patch.dict(os.environ,{'DATABASE_URL':test_url}):
            c=get_db_connection()
        try:
            c.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(namespace)))
            return c
        except Exception:
            c.close();raise
    with patch.dict(os.environ,{'DATABASE_URL':test_url}),get_db_connection() as c:
        c.execute('SET TRANSACTION READ ONLY');assert c.pgconn.ssl_in_use
    namespace='phishsense_review_'+uuid.uuid4().hex
    created=False;server=None
    password=secrets.token_urlsafe(18)
    try:
        with patch.dict(os.environ,{'DATABASE_URL':test_url}),get_db_connection() as c:
            c.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(namespace)))
        created=True
        with connect() as c:
            c.execute((ROOT/'schema.sql').read_text())
            assert seed_review(c,originals)==27
            for name,group in [('realism_adaptive','experimental'),('realism_control','control')]:
                c.execute('INSERT INTO users(username,email,password_hash,study_group) VALUES (%s,%s,%s,%s)',
                    (name,name+'@example.invalid',generate_password_hash(password,method='pbkdf2:sha256'),group))
        import app as application
        from flask import render_template,abort
        application.get_db_connection=connect
        app=application.app
        app.secret_key=secrets.token_hex(32)
        app.config['SESSION_COOKIE_NAME']='phishsense_realism_review_'+str(args.port)
        app.logger.disabled=True
        logging.getLogger('werkzeug').setLevel(logging.CRITICAL)
        revisions=load_review()
        styles=(ROOT/'templates/training.html').read_text().split('<style>',1)[1].split('</style>',1)[0]
        @app.route('/review')
        def review_index():
            with connect() as c:
                c.execute('SET TRANSACTION READ ONLY')
                scenarios=c.execute('SELECT * FROM training_scenarios ORDER BY scenario_id').fetchall()
            return render_template('scenario_review.html',scenarios=scenarios,revisions=revisions,styles=styles)
        with app.test_client() as client:
            assert client.get('/review').status_code==200
            for name in ('realism_adaptive','realism_control'):
                assert client.get('/login').status_code==200
                with client.session_transaction() as state:token=state['auth_form_token']
                assert client.post('/login',data=dict(email=name+'@example.invalid',password=password,auth_form_token=token)).status_code==302
                assert client.get('/dashboard').status_code==200
        path=Path('/private/tmp/PHISHSENSE_FINAL_REVIEW_ACCOUNTS.txt' if args.final else '/private/tmp/PHISHSENSE_REVISION3_REVIEW_ACCOUNTS.txt')
        path.write_text(f'Review all 27 emails: http://127.0.0.1:{args.port}/review\nLogin: http://127.0.0.1:{args.port}/login\nAdaptive: realism_adaptive@example.invalid\nControl: realism_control@example.invalid\nPassword for both: '+password+'\nDraft-only separate-project sandbox. No responses seeded.\n')
        path.chmod(0o600)
        Path('/private/tmp/phishsense_final_review_state.json' if args.final else '/private/tmp/phishsense_revision3_review_state.json').write_text(json.dumps(dict(schema=namespace,scenario_count=27,port=args.port,revision=3,refinement_pass="final-targeted" if args.final else None,content_sha256=hashlib.sha256((ROOT/"data/scenario_realism_drafts.json").read_bytes()).hexdigest())))
        # Single-threaded: scoped connection env patch cannot race another request.
        server=make_server('127.0.0.1',args.port,app,threaded=False)
        print(f'Draft review ready: http://127.0.0.1:{args.port}/review',flush=True)
        print('27 original numeric IDs preserved; 2 new synthetic accounts; credentials in local review file.',flush=True)
        server.serve_forever()
    finally:
        if server:server.server_close()
        if created:
            with patch.dict(os.environ,{'DATABASE_URL':test_url}),get_db_connection() as c:
                c.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(namespace)))


if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:pass
    except Exception as error:
        print('Review server stopped; error type:',type(error).__name__,flush=True)
        raise SystemExit(1)
