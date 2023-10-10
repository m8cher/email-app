# email-app
---

Read this in [Russian](./README.ru.md).

Package for working with email. Allows you to:
- send emails using an SMTP server;
- read emails using an IMAP server.

**Note**: The host and port of Google, Yandex, Mail (ru), Outlook, MSN services can be received using the [name](./email_app/servers.json) of the service. For other services, you must specify the host and port.

### Installation
---
Installation via pip:

```python
pip install git+https://github.com/m8cher/email-app.git
```

#### Sending an email
---
```python
from email_app import send_email


send_email(
    email='some_email@yandex.ru',
    password='some_password',
    domain='yandex',
    recievers=['reciever1@gmail.com', 'reciever2@yandex.ru'],
    subject='Some subject',
    message_text='Hello!',
    attachments=[r'path\to\pdf_file.pdf', r'path\to\excel_file.xlsx']
)
```
- `email` - sender email address;
- `password` - email app password;
- `recievers` - email recievers;

Additional parameters: 

- `domain` - domain of the email service. If None, will be received from the email address. Examples: google, yandex;
- `subject` - email subject;
- `message_text` - message text;
- `message_template` - path to the message template file (.txt or .html);
- `template_kwargs` - dictionary with values for template substitution;
- `attachments` - list of attachment files paths;
- `host` - SMTP-server host;
- `port` - SMTP-server port.

**Note**: You cannot set both `message_text` and `message_template`, `template_kwargs` parameters simultaneously. The `message_template` and `template_kwargs` parameters are always set together.

#### Reading an email
---

```python
from email_app import read_email


mails = read_email(
    email='some_email@yandex.ru',
    password='some_password',
    domain='yandex',
    mailbox='INBOX',
    criteria='UNSEEN',
    last=5,
    seen=False,
    with_payload=True
)
```
- `email` - email address which is read;
- `password` - email app password;
- `domain` - domain of the email service. If None, will be received from the email address. Examples: google, yandex;
- `mailbox` - mailbox section or folder name from which emails are read. Default: INBOX (incoming). Examples: Drafts, INBOX, Outbox, Sent, Spam, Trash, etc.;
- `criteria` - email search criteria, a complete list of criteria here. Example: UNSEEN SINCE 12-Dec-2022 - unread emails since December 12, 2022. The date format should be %d-%b-%Y;

Additional parameters:

- `last` - read the last n emails;
- `id_key` - email ID key. Example: "Message-ID" - for Yandex;
- `seen` - mark the email as "read." Default: True;
- `with_payload` - add payload for attached files;
- `folder` - folder path where attached files are saved;
- `host` - IMAP-server host;
- `port` - IMAP-server port.

**Note**: If a file with the same name as the attached file exists in the `folder`, the attached file is saved under modified name. Example: "test.xlsx" modified to "test (1).xlsx".

Returns a list of dictionaries containing the following email data: `subject`, `from`, `date`, `body` (email text), `attachments` (list of dictionaries with names of attachments, paths where attachments are saved if `folder` is set and payload if `with_payload` is True).

Email without saving attached files and without payload:
```
[{'subject': 'some subject',
  'from': 'email1@gmail.ru',
  'date': 'dd.MM.yyyy HH:mm:ss',
  'body': 'some message text',
  'attachments': [{'name': 'some_file.pdf'}]}]
```
Email with saved attachments and payload:
```
[{'subject': 'some subject',
  'from': 'email2@yandex.ru',
  'date': 'dd.MM.yyyy HH:mm:ss',
  'body': '',
  'attachments': [{'name': 'some_file.xlsx', 'path': 'path/to/some_file (1).xlsx', 'payload': b'some_payload'}]}]
```

**Note**: The original file name from the email is used for 'name' in `attachments`.

Cyrillic symbols in the folder name (`mailbox`) are set in bits, so you need to first get the folder name and then use it:

```python
import imaplib

from email_app import get_server

host, port = get_server('yandex', 'imap')
address = 'someemail@yandex.ru'
password = 'someapppassword'

with imaplib.IMAP4_SSL(host, port) as server:
    server.login(address, password)
    for mb in server.list()[1]:
        print(mb)
```
