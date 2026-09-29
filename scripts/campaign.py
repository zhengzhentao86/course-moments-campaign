#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local campaign bookkeeping. No network access or automatic publishing."""
import argparse
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sys
import tempfile


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def atomic_json(path, value):
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix='.campaign-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def calendar(start, days):
    if not 1 <= days <= 366:
        raise ValueError('days must be between 1 and 366')
    start = date.fromisoformat(start)
    return [{'days': d, 'publish_date': (start - timedelta(days=d)).isoformat()}
            for d in range(days, 0, -1)]


def init_workspace(path, course_id, name):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', course_id):
        raise ValueError('course-id must be lowercase letters, digits and hyphens')
    path = Path(path)
    if path.exists():
        raise ValueError('workspace already exists; read and update it, do not overwrite')
    path.mkdir(parents=True)
    for folder in ('evidence', 'campaigns'):
        (path / folder).mkdir()
    profile = {'schema_version': 1, 'course_id': course_id, 'name': name,
               'facts': {}, 'style_overrides': {}, 'sources': [], 'pending': []}
    atomic_json(path / 'course-profile.json', profile)
    (path / 'feedback.jsonl').touch()
    return {'created': str(path), 'course_id': course_id}


def record_feedback(workspace, item):
    import fcntl  # macOS/Linux; on other hosts use a platform-supported file lock.
    workspace = Path(workspace)
    profile = read(workspace / 'course-profile.json')
    required = ('id', 'course_id', 'kind', 'scope', 'source_ref', 'summary', 'action')
    if any(not isinstance(item.get(k), str) or not item[k].strip() for k in required):
        raise ValueError('missing nonempty feedback fields')
    if item['course_id'] != profile['course_id']:
        raise ValueError('feedback course_id differs from workspace')
    if item['kind'] not in ('editorial', 'course_fact', 'testimonial', 'measured_result', 'ai_suggestion'):
        raise ValueError('invalid feedback kind')
    if item['scope'] not in ('batch', 'course', 'cross_course'):
        raise ValueError('invalid scope')
    if item['scope'] == 'batch' and not item.get('campaign_id'):
        raise ValueError('batch scope requires campaign_id')
    if item['scope'] == 'cross_course' and not item.get('explicit_scope_quote'):
        raise ValueError('cross-course preference requires explicit scope evidence')
    if item['scope'] == 'cross_course' and item['kind'] not in ('editorial',):
        raise ValueError('course facts and results cannot become cross-course preferences')
    if not isinstance(item.get('supersedes', []), list):
        raise ValueError('supersedes must be a list')
    if item.get('status', 'active') not in ('active', 'pending'):
        raise ValueError('status must be active or pending')
    with (workspace / '.feedback.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = workspace / 'feedback.jsonl'
        old = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        by_id = {v['id']: v for v in old}
        if item['id'] in by_id:
            prior = by_id[item['id']]
            if all(prior.get(k) == v for k, v in item.items()):
                return {'duplicate_skipped': item['id']}
            raise ValueError('feedback id already used with different content')
        for key in item.get('supersedes', []):
            if key not in by_id:
                raise ValueError('superseded feedback does not exist')
            previous = by_id[key]
            if any(previous.get(k) != item.get(k) for k in ('course_id', 'scope', 'kind', 'rule_key')):
                raise ValueError('supersedes must target the same course, scope, kind and rule_key')
            if not item.get('rule_key'):
                raise ValueError('supersedes requires a nonempty rule_key')
            if item['scope'] == 'batch' and previous.get('campaign_id') != item.get('campaign_id'):
                raise ValueError('cannot supersede a different batch')
        value = dict(item)
        value.setdefault('recorded_at', datetime.now(timezone.utc).isoformat())
        value.setdefault('status', 'active')
        with path.open('a', encoding='utf-8') as out:
            out.write(json.dumps(value, ensure_ascii=False) + '\n')
            out.flush()
            os.fsync(out.fileno())
    return {'recorded': item['id'], 'status': value['status']}


def check_campaign(path, draft=False):
    path = Path(path).resolve()
    data = read(path)
    errors = []
    posts = data.get('posts', [])
    if not isinstance(posts, list) or not posts:
        return ['posts must be a nonempty list']
    expected = data.get('expected_count')
    if type(expected) is not int or expected != len(posts):
        errors.append('expected_count differs from actual count or is not an integer')
    ids, images, days_seen = set(), set(), []
    for i, post in enumerate(posts, 1):
        prefix = 'post ' + str(i) + ': '
        if not isinstance(post, dict):
            errors.append(prefix + 'must be an object')
            continue
        pid = post.get('id')
        if not isinstance(pid, (int, str)) or isinstance(pid, bool) or not str(pid).strip() or str(pid) in ids:
            errors.append(prefix + 'missing or duplicate id')
        ids.add(str(pid))
        for field in ('title', 'text', 'audience_problem', 'course_method', 'practical_output', 'poster_prompt'):
            if not isinstance(post.get(field), str) or not post[field].strip():
                errors.append(prefix + 'missing ' + field)
        if not isinstance(post.get('source_refs'), list) or not post['source_refs']:
            errors.append(prefix + 'missing source_refs')
        if not draft:
            rel = post.get('image')
            if not isinstance(rel, str) or not rel:
                errors.append(prefix + 'missing image')
            else:
                image = (path.parent / rel).resolve()
                try:
                    image.relative_to(path.parent)
                    if Path(rel).is_absolute():
                        raise ValueError()
                    if not image.is_file() or image.stat().st_size == 0:
                        errors.append(prefix + 'image missing or empty')
                except ValueError:
                    errors.append(prefix + 'image must stay within campaign directory')
                if str(image) in images:
                    errors.append(prefix + 'reused image file')
                images.add(str(image))
            for field in ('copy_reviewed', 'visual_reviewed'):
                if post.get(field) is not True:
                    errors.append(prefix + field + ' is not true')
        if data.get('mode') == 'countdown':
            try:
                d = post['days']
                if type(d) is not int or d < 1:
                    raise ValueError()
                actual = (date.fromisoformat(data['start_date']) - date.fromisoformat(post['publish_date'])).days
                if actual != d:
                    errors.append(prefix + 'countdown/date mismatch')
                days_seen.append(d)
            except (KeyError, TypeError, ValueError):
                errors.append(prefix + 'missing or invalid countdown date/day')
    if data.get('mode') == 'countdown' and days_seen != list(range(len(posts), 0, -1)):
        errors.append('countdown must cover N through 1 in descending order')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('init')
    p.add_argument('--workspace', required=True)
    p.add_argument('--course-id', required=True)
    p.add_argument('--name', required=True)
    p = sub.add_parser('calendar')
    p.add_argument('--start-date', required=True, help='Course local calendar date YYYY-MM-DD')
    p.add_argument('--days', type=int, default=10)
    p = sub.add_parser('record-feedback')
    p.add_argument('--workspace', required=True)
    p.add_argument('--file', required=True)
    p = sub.add_parser('check')
    p.add_argument('--file', required=True)
    p.add_argument('--draft', action='store_true', help='Skip image/review completion checks')
    args = parser.parse_args()
    try:
        if args.command == 'init':
            result = init_workspace(args.workspace, args.course_id, args.name)
        elif args.command == 'calendar':
            result = calendar(args.start_date, args.days)
        elif args.command == 'record-feedback':
            result = record_feedback(args.workspace, read(args.file))
        else:
            errors = check_campaign(args.file, args.draft)
            print(json.dumps({'ok': not errors, 'errors': errors,
                              'scope': 'structure-only; no semantic, image-content or delivery validation'}, ensure_ascii=False, indent=2))
            return 1 if errors else 0
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
