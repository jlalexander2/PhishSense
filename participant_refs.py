"""Opaque per-learner/session item references; numeric plans stay in PostgreSQL."""
import hashlib
import hmac
import re


def item_reference(secret, user_id, session_id, scenario_id, nonce):
    key=secret.encode() if isinstance(secret,str) else secret
    message=f'phishsense-item-v1|{user_id}|{session_id}|{scenario_id}|{nonce}'.encode()
    return hmac.new(key,message,hashlib.sha256).hexdigest()


def resolve_reference(secret, user_id, session_id, ids, nonce, reference):
    if not isinstance(reference,str) or not re.fullmatch('[0-9a-f]{64}',reference) or not nonce:
        return None
    return next((sid for sid in ids if hmac.compare_digest(
        item_reference(secret,user_id,session_id,sid,nonce),reference)),None)
