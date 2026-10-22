#!/usr/bin/env python3
"""Reject unreviewed outbound transports and committed SMTP source files."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path.cwd()
SOURCE = '/etc/actigence/mail/smtp2go.env'
SENDER = re.compile(r'smtplib\.SMTP(?:_SSL)?\b|from\s+smtplib\s+import|new\s+(?:EsmtpTransport|SmtpTransport|SendmailTransport|Resend|SendGrid|Mailgun)\b|createTransport\s*\(|MAIL FROM:|/usr/sbin/sendmail|adapter:\s*Bamboo\.Mua|Bamboo\.Mua\.deliver|\b(?:resend|sendgrid|mailgun)\.(?:emails|Emails|client|send|Resend|SendGridAPIClient)|smtps?://|smtp\.SendMail\s*\(|Net::SMTP\b|boto3\.client\(\s*[\x27\x22]ses[\x27\x22]|\b(?:SendEmailCommand|SendRawEmailCommand)\b|dawidd6/action-send-mail')
EXTERNAL = re.compile(r'api\.(?:resend|sendgrid|mailgun|postmarkapp)\.com|smtp\.(?:gmail|office365)\.com|https://api\.smtp2go\.com')
EXTENSIONS = {'.py', '.php', '.ts', '.mjs', '.cjs', '.mts', '.js', '.ex', '.exs', '.sh', '.rb', '.go', '.rs', '.yml', '.yaml'}


def eligible(name):
    p = Path(name)
    if p.suffix not in EXTENSIONS:
        return False
    if '.github' in p.parts and '.github/workflows/' not in p.as_posix():
        return False
    if any(part in {'.planning', 'node_modules', 'tests', 'test', 'reference', 'docs', 'docs-site', 'qualification'} for part in p.parts):
        return False
    return not (p.name.startswith(('test_', 'test-', 'qualify', 'verify-')) or '.test.' in p.name or '.spec.' in p.name)


def sender(name, text):
    if SENDER.search(text):
        return True
    if Path(name).suffix == '.php':
        # PHP's global mail() is a transport. A method named mail in another
        # language or a prose comment is not evidence of an outbound transport.
        code = re.sub(r'\{\{--.*?--\}\}', '', text, flags=re.S)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.S)
        code = re.sub(r'^\s*//.*$', '', code, flags=re.M)
        return bool(re.search(r'(?<!->)(?<!::)\bmail\s*\(', code))
    return False


def tracked():
    result = subprocess.run(['git', 'ls-files', '-z'], capture_output=True, check=True)
    return [name for name in result.stdout.decode().split('\0') if name]


def check(names):
    errors = []
    manifest = json.loads((ROOT/'mail-consumer.json').read_text())
    if (manifest.get('schema') != 'actigence.mail.consumer.v1' or manifest.get('smtpSource') != SOURCE
            or manifest.get('delivery') != 'actigence-mail-only' or manifest.get('fallback') != 'refuse'):
        errors.append('mandatory_mail_contract_invalid')
    approved = manifest.get('approvedAdapters', {})
    dependencies = manifest.get('inactiveDependencyTransports', {})
    for name in names:
        if Path(name).name == 'smtp2go.env':
            errors.append('smtp_source_must_never_be_committed')
        if not eligible(name):
            continue
        p = ROOT/name
        if not p.is_file():
            continue
        text = p.read_text(encoding='utf-8')
        if EXTERNAL.search(text):
            exception = manifest.get('nonDeliveryClients', {}).get(name, {})
            if exception.get('sha256') != hashlib.sha256(p.read_bytes()).hexdigest() or not exception.get('reason'):
                errors.append(f'{name}: external_mail_provider_forbidden')
        if sender(name, text):
            dependency = dependencies.get(name, {})
            if dependency.get('sha256') == hashlib.sha256(p.read_bytes()).hexdigest() and dependency.get('reason'):
                continue
            expected = approved.get(name)
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            if not expected or expected.get('sha256') != digest or expected.get('via') not in {'actigence-mail-private-relay', 'actigence-mail-upstream'}:
                errors.append(f'{name}: outbound_transport_requires_review')
    for name, adapter in {**dependencies, **approved}.items():
        p = ROOT/name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != adapter.get('sha256'):
            errors.append(f'{name}: approved_adapter_changed_or_missing')
    for name in ['AGENTS.md', 'docs/MAIL-MANDATORY.md']:
        if SOURCE not in (ROOT/name).read_text():
            errors.append(f'{name}: source_rule_missing')
    return errors


if __name__ == '__main__':
    try:
        errors = check(tracked())
    except (OSError, ValueError, subprocess.CalledProcessError):
        errors = ['mail_contract_unreadable']
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        sys.exit(1)
    print('Actigence Mail mandatory contract and reviewed adapters: OK')
