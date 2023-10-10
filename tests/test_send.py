import os
import unittest

from dotenv import load_dotenv
from email_app.send import send_email


load_dotenv()


EMAIL = os.environ.get('EMAIL')
PASSWORD = os.environ.get('PASSWORD')
DOMAIN = 'yandex'
RECIEVER = os.environ.get('RECIEVER')
FOLDER = os.path.join(os.path.dirname(__file__), 'attachments')


class SendEmail(unittest.TestCase):
    def test_send_email_without_attachments(self):
        send_email(
            email=EMAIL,
            password=PASSWORD,
            domain=DOMAIN,
            recievers=[RECIEVER],
            subject='Subject',
            message_text='Hello!'
        )

    def test_send_email_with_attachments(self):
        send_email(
            email=EMAIL,
            password=PASSWORD,
            domain=DOMAIN,
            recievers=[RECIEVER],
            subject='Subject',
            message_text='Hello!',
            attachments=[
                os.path.join(FOLDER, 'test.xlsx'),
                os.path.join(FOLDER, 'test.pdf')
            ]
        )
