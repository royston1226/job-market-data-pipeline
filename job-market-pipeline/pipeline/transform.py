"""Pure transformations. Preserve unknown source categories rather than guessing."""
from datetime import datetime, timezone
import re
from urllib.parse import urlsplit

TEXT_FIELDS = ['id', 'job_id', 'title', 'department', 'employment_type',
               'workplace_type', 'country', 'apply_url', 'status']
DATE_FIELDS = ['posted_at', 'fetched_time', 'close_time']

def clean_text(value):
    if value is None:
        return None
    result = re.sub(r'\s+', ' ', str(value)).strip()
    return result or None

def clean_date(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

def transform(raw):
    row = {k: clean_text(raw.get(k)) for k in TEXT_FIELDS}
    if not row['id'] or not row['title']:
        raise ValueError('missing id or title')
    row['company_id'] = int(raw['company_id'])
    remote = raw.get('is_remote')
    if not isinstance(remote, bool):
        raise ValueError('is_remote must be boolean')
    row['is_remote'] = remote
    for k in DATE_FIELDS:
        row[k] = clean_date(raw.get(k))
    for k in ['workplace_type', 'status']:
        if row[k]:
            row[k] = row[k].lower()
    employment = row['employment_type']
    if employment:
        key = employment.lower().replace('-', ' ')
        row['employment_type'] = {'full time': 'full-time', 'part time': 'part-time'}.get(key, key)
    warnings = []
    if row['apply_url']:
        url = urlsplit(row['apply_url'])
        if url.scheme not in ('http', 'https') or not url.netloc:
            warnings.append('invalid_apply_url')
            row['apply_url'] = None
    start, end = row['posted_at'], row['close_time']
    row['duration_days'] = None
    if start and end:
        if end < start:
            warnings.append('close_before_post')
        elif row['status'] == 'closed':
            row['duration_days'] = (end-start).total_seconds()/86400
    if row['is_remote'] and row['workplace_type'] == 'onsite':
        warnings.append('remote_onsite_conflict')
    row['quality_flags'] = warnings
    return row
