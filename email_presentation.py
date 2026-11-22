"""Render email evidence as escaped text and inert, inspectable UI components.

No HTML parsing, network requests, classification-based styling or draft overlays.
"""
import re
from urllib.parse import urlsplit, unquote

TOKEN = re.compile(r'\[\[link:([^\]\n|]{1,200})\|([^\]]+)\]\]|\[\[attachment:([^\]\n|]+)(?:\|([^\]\n]*))?\]\]|\[(?:simulated|Simulated) attachment: ([^\]\n]+)\]|https?://[^\s<>\[\]"\']+')


def safe_destination(value):
    """HTTPS, reserved fictional DNS name, no credentials/ports/ambiguous encoding."""
    if not isinstance(value, str) or len(value) > 2048:
        return False
    decoded = unquote(value)
    if any(ord(c) < 33 or ord(c) > 126 for c in decoded) or any(c in decoded for c in ('\\', '"', '<', '>', "'")):
        return False
    try:
        parts = urlsplit(value)
        host = parts.hostname or ''
        return (parts.scheme == 'https' and not parts.username and not parts.password and
                parts.port is None and parts.netloc == host and
                host.endswith(('.example', '.test')) and
                all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label)
                    for label in host.split('.')))
    except ValueError:
        return False


def body_parts(body):
    parts = []
    offset = 0
    for match in TOKEN.finditer(body):
        if match.start() > offset:
            parts.append(dict(kind='text', text=body[offset:match.start()]))
        label, destination, filename, preview, legacy = match.groups()
        if label and safe_destination(destination):
            parts.append(dict(kind='link', label=label, destination=destination))
        elif filename:
            parts.append(dict(kind='attachment', filename=filename.strip(), preview=preview or ''))
        elif legacy:
            # Remove only the renderer's safety wrapper, preserving file/contents evidence.
            content = re.sub(r'\s*[—–-]\s*not downloadable\s*$', '', legacy)
            name, separator, detail = content.partition(';')
            parts.append(dict(kind='attachment', filename=name.strip(), preview=detail.strip() if separator else ''))
        elif not label and safe_destination(match.group(0).rstrip('.,;!?)')):
            url = match.group(0).rstrip('.,;!?)')
            parts.append(dict(kind='link', label=url, destination=url))
            suffix = match.group(0)[len(url):]
            if suffix:
                parts.append(dict(kind='text', text=suffix))
        else:
            parts.append(dict(kind='text', text=match.group(0)))
        offset = match.end()
    if offset < len(body):
        parts.append(dict(kind='text', text=body[offset:]))
    return parts


def present_email(scenario):
    body = scenario.get('email_body') or ''
    context = scenario.get('training_context') or ''
    prefix = 'TRAINING CONTEXT (not part of the email):\n'+context+'\n\nEMAIL MESSAGE:\n'
    if context and body.startswith(prefix):
        body = body[len(prefix):]
    metadata = scenario.get('presentation_metadata') or {}
    if not isinstance(metadata, dict):
        metadata = {}
    reply_to = metadata.get('reply_to', '')
    if not isinstance(reply_to, str) or not re.fullmatch(r"[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9.-]+\.(?:example|test)", reply_to):
        reply_to = ''
    inspected = {}
    for entry in metadata.get('links', []) if isinstance(metadata.get('links'), list) else []:
        if not isinstance(entry, dict) or not safe_destination(entry.get('destination')):
            continue
        name = entry.get('application_name', '')
        permissions = entry.get('permissions', [])
        if isinstance(name, str) and isinstance(permissions, list) and all(isinstance(p, str) for p in permissions):
            inspected[entry['destination']] = dict(application_name=name, permissions=permissions)
    parts = body_parts(body)
    for part in parts:
        if part['kind'] == 'link' and part['destination'] in inspected:
            part['inspection'] = inspected[part['destination']]
    # Never project IDs, ratings, classifications or reviewer metadata.
    return dict(context=context, parts=parts, reply_to=reply_to)
