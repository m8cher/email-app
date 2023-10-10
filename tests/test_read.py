import os
import unittest

from dotenv import load_dotenv
from email_app import read_email


load_dotenv()


EMAIL = os.environ.get('EMAIL')
PASSWORD = os.environ.get('PASSWORD')
DOMAIN = 'yandex'
FOLDER = os.path.join(os.path.dirname(__file__), 'attachments')


class ReadEmail(unittest.TestCase):
    def test_read_email_with_payload(self):
        mails = read_email(
            email=EMAIL,
            password=PASSWORD,
            domain=DOMAIN,
            mailbox='INBOX',
            criteria='UNSEEN',
            last=5,
            seen=False,
            with_payload=True
        )
        print(mails)

    def test_read_email_with_saving(self):
        mails = read_email(
            email=EMAIL,
            password=PASSWORD,
            domain=DOMAIN,
            mailbox='INBOX',
            criteria='UNSEEN',
            last=5,
            seen=False,
            with_payload=False,
            folder=FOLDER
        )
        print(mails)
