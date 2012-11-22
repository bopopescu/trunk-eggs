import os
import time
import random
from email import message_from_file
import tempfile
import shutil
import unittest

from mock import patch

from Products.Naaya.tests.NaayaTestCase import FunctionalTestCase
from Products.NaayaCore.EmailTool.EmailTool import EmailTool, create_message, save_bulk_email

class EmailTestCase(FunctionalTestCase):
    def test_mail(self):
        self.portal.getEmailTool().sendEmail('test_content',
            'test_to@example.com', 'test_from@example.com', 'test_subject')

        smtp_log = self.mail_log

        self.failUnlessEqual(len(smtp_log), 3)
        self.failUnlessEqual(smtp_log[0][0], 'init')
        self.failUnlessEqual(smtp_log[1][0], 'sendmail')
        self.failUnlessEqual(smtp_log[2][0], 'quit')

        self.failUnlessEqual(smtp_log[1][1]['from'], 'test_from@example.com')
        self.failUnlessEqual(smtp_log[1][1]['to'], ['test_to@example.com'])
        self.failUnless('Subject: test_subject\n' in smtp_log[1][1]['message'])
        self.failUnless('test_content' in smtp_log[1][1]['message'])
        self.failUnless('Content-Type: text/plain;' in
                        smtp_log[1][1]['message'])

    def test_mail_from(self):
        self.portal.getEmailTool().sendEmail('test_content',
            'test_to_1@example.com, test_to_2@example.com',
            'test_from@example.com', 'test_subject')

        smtp_log = self.mail_log
        self.assertEqual(len(smtp_log), 3)
        to = smtp_log[1][1]['to']

        self.failUnlessEqual(len(to), 2)
        self.failUnless('test_to_1@example.com' in to)
        self.failUnless('test_to_2@example.com' in to)

class EmailSaveTestCase(unittest.TestCase):
    def setUp(self):
        from App.config import getConfiguration
        from Products.Naaya.NySite import NySite

        self.config = getConfiguration()
        self.config_patch = patch.object(self.config, 'environment', {},
                                         create=True)
        self.config_patch.start()

        self.environ_patch = patch.dict(os.environ)
        self.environ_patch.start()

        self.portal = NySite('test')
        self.portal.portal_email = EmailTool('id_email_tool', 'Test email tool')

        self.TMP_FOLDER = tempfile.mkdtemp()

    def tearDown(self):
        self.environ_patch.stop()
        self.config_patch.stop()
        shutil.rmtree(self.TMP_FOLDER)

    @patch('Products.NaayaCore.EmailTool.EmailTool.get_zope_env')
    def test_save_mail(self, get_zope_env):
        get_zope_env.return_value = self.TMP_FOLDER
        filename = save_bulk_email(self.portal.id, ['to1@edw.ro', 'to2@edw.ro'],
                                   'from@edw.ro', 'Hello!', 'Hello World!')
        self.assertTrue(os.path.isfile(filename))
        message_file = open(filename, 'r+')
        mail = message_from_file(message_file)
        message_file.close()

        self.assertEqual(mail.get('Subject'), 'Hello!')
        self.assertEqual(mail.get_payload(), 'Hello World!')
        self.assertEqual(mail.get_all('To'), ['to1@edw.ro', 'to2@edw.ro'])
        self.assertEqual(mail.get('From'), 'from@edw.ro')

        emails = self.portal.getEmailTool().get_saved_bulk_emails()

        self.assertEqual(len(emails), 1)
        self.failUnless('content' in emails[0])
        self.failUnless('date' in emails[0])
        self.failUnless('subject' in emails[0])
        self.failUnless('sender' in emails[0])
        self.failUnless('recipients' in emails[0])

        self.assertEqual(emails[0]['content'], 'Hello World!')
        self.assertEqual(emails[0]['subject'], 'Hello!')
        self.assertEqual(emails[0]['sender'], 'from@edw.ro')
        self.assertEqual(emails[0]['recipients'], ['to1@edw.ro', 'to2@edw.ro'])
