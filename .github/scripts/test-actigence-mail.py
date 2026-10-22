import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('mail_guard', Path(__file__).with_name('check-actigence-mail.py'))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.previous_root = guard.ROOT
        guard.ROOT = self.root
        (self.root/'docs').mkdir()
        for name in ['AGENTS.md', 'docs/MAIL-MANDATORY.md']:
            (self.root/name).write_text(guard.SOURCE)
        (self.root/'mail-consumer.json').write_text(json.dumps({
            'schema':'actigence.mail.consumer.v1', 'smtpSource':guard.SOURCE,
            'delivery':'actigence-mail-only', 'fallback':'refuse', 'approvedAdapters':{}}))

    def tearDown(self):
        guard.ROOT = self.previous_root
        self.directory.cleanup()

    def test_new_senders_and_http_provider_are_rejected(self):
        cases = {
            'vendor/owned-mail.py': 'from smtplib import SMTP\nSMTP("bad.invalid",25)',
            'resend.py': 'import resend\nresend.Emails.send({})',
            'new_sender.py': 'from smtplib import SMTP\nSMTP("bad.invalid", 25)\n',
            'new_sender.php': '<?php mail("a@example.invalid", "subject", "body");',
            'new_sender.ts': 'import resend from "resend"; resend.emails.send({});',
            'new_sender.sh': 'curl https://api.resend.com/emails -d "{}"',
            'smtp.go': 'smtp.SendMail("bad.invalid:25", nil, "a@b.invalid", []string{"c@d.invalid"}, nil)',
            'smtp.rb': 'Net::SMTP.start("bad.invalid", 25) {}',
            'ses.py': 'import boto3\nboto3.client("ses").send_email()',
            'send.ex': 'Bamboo.Mua.deliver(email, config)',
            'smtp.sh': 'curl smtp://bad.invalid --mail-rcpt c@example.invalid',
            '.github/workflows/send.yml': 'jobs:\n  send:\n    steps:\n      - run: curl smtp://bad.invalid',
        }
        for name, code in cases.items():
            with self.subTest(name=name):
                (self.root/name).parent.mkdir(parents=True, exist_ok=True)
                (self.root/name).write_text(code)
                self.assertTrue(guard.check([name]))

    def test_canonical_source_can_never_be_tracked(self):
        self.assertIn('smtp_source_must_never_be_committed', guard.check(['smtp2go.env']))

    def test_approved_adapter_changes_are_detected(self):
        import hashlib
        p=self.root/'adapter.py';p.write_text('from smtplib import SMTP\n')
        manifest=json.loads((self.root/'mail-consumer.json').read_text())
        manifest['approvedAdapters']={'adapter.py':{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'via':'actigence-mail-private-relay'}}
        (self.root/'mail-consumer.json').write_text(json.dumps(manifest))
        self.assertEqual(guard.check(['adapter.py']),[])
        p.write_text('from smtplib import SMTP\nSMTP("bad.invalid",25)')
        self.assertTrue(guard.check(['adapter.py']))


if __name__ == '__main__':
    unittest.main()
