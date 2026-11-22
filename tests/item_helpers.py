"""Test fixtures use known numeric IDs; browser requests use real opaque references."""
from participant_refs import item_reference


def stored_plan(postgres,state):
    with postgres() as c:
        row=c.execute('SELECT scenario_ids FROM training_sessions WHERE session_id=%s AND user_id=%s',
                      (state['training_session_id'],state['user_id'])).fetchone()
    return row['scenario_ids'] if row else []


def reference(client,sid,state=None):
    import app
    if state is None:
        with client.session_transaction() as cookie:
            values=dict(cookie)
        state=values
    return item_reference(app.app.secret_key,state['user_id'],state.get('training_session_id',1),sid,state.get('training_nonce','fixture-nonce'))


def open_item(client,sid):
    return client.get('/training',query_string={'item_ref':reference(client,sid)})


def submit_item(client,data):
    payload=dict(data);sid=payload.pop('scenario_id',None)
    payload['item_ref']=reference(client,sid) if type(sid) is int else 'invalid'
    return client.post('/training',data=payload)
