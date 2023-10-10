# email-app
---

Пакет для работы с электронной почтой. Позволяет:
- отправлять письма с помощью SMTP-сервера
- читать письма с помощью IMAP-сервера.

**Примечание**: хост и порт Google, Yandex, Mail (ru), Outlook, MSN сервисов могут быть получены с помощью [названия](./email_app/servers.json) сервисов. Для других сервисов необходимо указать хост и порт.

### Установка
---
Установка через `pip`:

```python
pip install git+https://github.com/m8cher/email-app.git
```

#### Отправка электронного письма
---
```python
from email_app import send_email


send_email(
    email='some_email@yandex.ru',
    password='some_password',
    domain='yandex',
    recievers=['reciever1@gmail.com', 'reciever2@yandex.ru'],
    subject='Тема',
    message_text='hello',
    attachments=['path/to/pdf_file.pdf', 'path/to/excel_file.xlsx']
)
```
- `email` - email отправителя;
- `password` - пароль, созданный для почтовой программы;
- `recievers` - список email получателей;

Дополнительные параметры:  

- `domain` - домен почтового сервиса. Если None, получаем из email;
- `subject` - тема письма;
- `message_text` - текст сообщения;
- `message_template` - путь к файлу с шаблоном сообщения (.txt или .html);
- `template_kwargs` - словарь со значениями для подстановки в шаблон;
- `attachments` - список путей к файлам вложений;
- `host` - хост SMTP-сервера;
- `port` - порт SMTP-сервера.

**Примечание:** Нельзя задавать параметры `message_text` и `message_template`, `template_kwargs` одновременно. Параметры `message_template` и `template_kwargs` всегда задаются вместе.

#### Чтение электронного письма
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
- `email` - email владельца почты;
- `password` - пароль, созданный для почтовой программы;
- `domain` - домен почтового сервиса. Если None, получаем из email;
- `mailbox` - раздел почты или название папки, откуда читаются письма. По умолчанию: INBOX (входящие). Примеры: Drafts, INBOX, Outbox, Sent, Spam, Trash и тд.;
- `criteria` - критерии поиска писем, полный список критериев [здесь](https://www.rfc-editor.org/rfc/rfc3501#section-6.4.4). Пример: UNSEEN SINCE 12-Dec-2022 - непрочитанные письма с 12.12.2022. Формат даты должен быть %d-%b-%Y;

Дополнительные параметры:  

- `last` - чтение последних n писем;
- `id_key` - ключ, под которым хранится ID письма. Пример: для yandex Message-ID;
- `seen` - прометка письма "прочитанным". По умолчанию: True;
- `with_payload` - добавление payload прикрепленных файлов;
- `folder` - путь к папке для сохранения прикрепленных файлов.
- `host` - хост IMAP-сервера;
- `port` - порт IMAP-сервера.

**Примечание**: Если существует файл с таким же названием, как у прикрепленного файла, в `folder`, то прикрепленный файл сохраняется под измененным названием. Например: "test.xlsx" изменится на "test (1).xlsx".

Возвращает список словарей прочитанных писем со следующими данными: `subject`, `from`, `date`, `body` (текст письма), `attachments` (список словарей из названий прикрепленных файлов, путей к сохраненным файлам при задании `folder` и с добавлением payload при `with_payload` равным True).

Письма без сохранения прикрепленных файлов и добавления payload:
```
[{'subject': 'some subject',
  'from': 'email1@gmail.ru',
  'date': 'dd.MM.yyyy HH:mm:ss',
  'body': 'some message text',
  'attachments': [{'name': 'some_file.pdf'}]}]
```
Письма с сохранением прикрепленных файлов и с добавлением payload:
```
[{'subject': 'some subject',
  'from': 'email2@yandex.ru',
  'date': 'dd.MM.yyyy HH:mm:ss',
  'body': '',
  'attachments': [{name': 'some_file.xlsx', 'path': 'path/to/some_file (1).xlsx', 'payload': b'some_payload'}]}]
```

**Примечание:** В `attachments` для ключа 'name' используется исходное название файла из письма.

Кириллица в названии папки (`mailbox`) задается в битах, поэтому необходимо сначала получить название папки, и потом использовать его:

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
