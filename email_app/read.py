import base64
import email
from email.header import decode_header, make_header
from datetime import datetime
import imaplib
import logging
import os
from pathlib import Path
import quopri

from bs4 import BeautifulSoup

from .types import ReadEmailParams
from .utils import get_server, build_filepath


def get_header(message_header: str):
    """Decode email subject and sender.

    message_header   str;

    return           str.
    """
    return str(make_header(decode_header(message_header)))


def get_date(message_date: str):
    """Get email sending date.

    message_date    str;

    return          str.
    """
    date_tuple = email.utils.parsedate_tz(message_date)
    if date_tuple:
        date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
        date = str(date.strftime('%d.%m.%Y %H:%M:%S'))
        return date


def get_headers(message: email.message.Message):
    """Get email headers.

    message    email.message.Message object;

    return     tuple.
    """
    subject = get_header(message.get('Subject', '(No subject)'))
    From = get_header(message.get('From'))
    date = get_date(message.get('Date'))
    return subject, From, date


def get_html_text(body: str):
    """Get email HTML body text.

    body      email HTML body;

    return    str.
    """
    logger = logging.getLogger(__name__)
    try:
        soup = BeautifulSoup(body, 'html.parser')
        return soup.get_text().replace('\xa0', ' ')
    except (Exception) as exp:
        logger.error('text from html err:', exp)
        return False


def decode_text(message: email.message.Message):
    """Decode email text.

    message    email.message.Message object;

    return     str.
    """
    if message['Content-Transfer-Encoding'] in (
        None, '7bit', '8bit', 'binary'
    ):
        return message.get_payload()
    elif message['Content-Transfer-Encoding'] == 'base64':
        encoding = message.get_content_charset()
        return base64.b64decode(message.get_payload()).decode(encoding)
    elif message['Content-Transfer-Encoding'] == 'quoted-printable':
        encoding = message.get_content_charset()
        return quopri.decodestring(message.get_payload()).decode(encoding)
    else:
        # all possible types: quoted-printable, base64, 7bit, 8bit, and binary
        return message.get_payload()


def get_text(message: email.message.Message):
    """Get email text.

    message    email.message.Message object;

    return     str.
    """
    extract_part = decode_text(message)
    if message.get_content_subtype() == 'html':
        text = get_html_text(extract_part)
    else:
        text = extract_part.rstrip().lstrip()
    return text.replace('<', '').replace('>', '').replace('\xa0', ' ')


def get_attachment(
    message: email.message.Message,
    with_payload: bool = False,
    folder: Path = None
):
    """Get email attachment files as a dictionary with name, path, payload.

    message         email.message.Message object;
    with_payload    add payload to the attached files;
    folder          folder path where attached files are saved;

    return          dict.
    """
    logger = logging.getLogger(__name__)
    filename = message.get_filename()
    payload = message.get_payload(decode=True)
    if filename:
        result = {'name': filename}
        if folder:
            filepath = build_filepath(os.path.join(folder, filename))
            # Save file
            open(filepath, "wb").write(payload)
            logger.info(f"Attached file '{filename}' saved")
            result.update({'path': filepath})
        if with_payload:
            result.update({'payload': payload})
        return result


def get_email(
    server: imaplib.IMAP4_SSL,
    num: bytes,
    id_key: str = None,
    seen: bool = True,
    with_payload: bool = False,
    folder: Path = None
):
    """Get email as a dictinary with subject, from, date, body, attachments
    keys.

    server          imaplib.IMAP4_SSL object;
    num             email number;
    id_key          email ID key. Example: "Message-ID" - for Yandex;
    seen            mark the email as "read." Default: True;
    with_payload    add payload for attached files;
    folder          folder path where attached files are saved;

    return          dict.
    """
    logger = logging.getLogger(__name__)
    result, data = server.fetch(num, '(RFC822)')
    for response in data:
        if isinstance(response, tuple):
            message = email.message_from_bytes(response[1])
            subject, From, date = get_headers(message)
            msg = {} if id_key is None else {'id': str(message.get(id_key))}
            msg = msg | {'subject': subject, 'from': From, 'date': date}
            logger.debug(f"Email {num} object received")
            if message.is_multipart():
                logger.info(f"Email '{num}' is multipart")
                # count = 0
                for part in message.walk():
                    if part.get_content_maintype() == 'text':  # and count==0:
                        text = get_text(part)
                        msg['body'] = text
                        logger.debug('Email text received')
                        # count += 1
                    if 'attachment' in str(part.get('Content-Disposition')):
                        file = get_attachment(
                            message=part,
                            with_payload=with_payload,
                            folder=folder
                        )
                        if msg.get('attachments', None):
                            msg['attachments'].append(file)
                        else:
                            msg['attachments'] = [file]
            else:
                # Email containes only text
                if message.get_content_maintype() == 'text':
                    logger.info(f"Email '{num}' contains only text")
                    text = get_text(message)
                    msg['body'] = text
                    logger.debug('Email text received')
    if seen:
        server.store(num, '+FLAGS', '\\Seen')
        logger.info(f"Email '{num}' marked as 'unseen'")
    else:
        server.store(num, '-FLAGS', '\\Seen')
        logger.info(f"Email '{num}' marked as 'unseen'")
    return msg


def get_emails(
    server: imaplib.IMAP4_SSL,
    criteria: str = 'ALL',
    last: int = None,
    id_key: str = None,
    seen: bool = True,
    with_payload: bool = False,
    folder: Path = None
):
    """Get emails as a list of dictinaries with subject, from, date, body,
    attachments.

    keys.
    server          imaplib.IMAP4_SSL object;
    criteria        email search criteria. Examples:
                    'ALL' - all emails,
                    'UNSEEN' - only unseen emails,
                    'SINCE 12-Dec-2022' - from date in format %d-%b-%Y,
                    'UNSEEN SINCE 12-Dec-2022' - several criteria;
    last            read the last n emails;
    id_key          email ID key. Example: "Message-ID" - for Yandex;
    seen            mark the email as "read." Default: True;
    with_payload    add payload for attached files;
    folder          folder path where attached files are saved;

    return          list[dict].
    """
    status, data = server.search(None, criteria)
    nums = data[0].split()
    emails = []
    if last:
        nums = nums[-last:]
    for num in nums:
        emails.append(
            get_email(
                server=server,
                num=num,
                id_key=id_key,
                seen=seen,
                with_payload=with_payload,
                folder=folder
            )
        )
    return emails


def read_email(
    email: str,
    password: str,
    domain: str = None,
    mailbox='INBOX',
    criteria: str = 'ALL',
    last: int = None,
    id_key: str = None,
    seen: str = None,
    with_payload: bool = None,
    folder: Path = None,
    host: str = None,
    port: int = None
):
    """Read email message and get attachment files with or without payload.

    email           email address which is read;
    password        email app password;
    domain          domain of the email service.
                    If None, will be received from email;
                    Examples: google, yandex
    mailbox         mailbox section or folder name from which emails are read.
                    Default: INBOX (incoming).
                    Examples: Drafts, INBOX, Outbox, Sent, Spam, Trash, etc.;
    criteria        email search criteria. Examples:
                    'ALL' - all emails,
                    'UNSEEN' - only unseen emails,
                    'SINCE 12-Dec-2022' - from date in format %d-%b-%Y,
                    'UNSEEN SINCE 12-Dec-2022' - several criteria;

    Additional parameters:
    last            read the last n emails;
    id_key          email ID key.. Example: "Message-ID" - for Yandex;
    seen            mark the email as "read." Default: True;
    with_payload    add payload for attached files;
    folder          folder path where attached files are saved;
    host            IMAP-server host;
    port            IMAP-server port.

    return          list[dict].
    """
    logger = logging.getLogger(__name__)

    # Create folder, if not exist
    if folder:
        if not os.path.exists(folder):
            os.mkdir(folder)
            logger.debug(f"Created a folder '{folder}'")

    # Check parameters
    params = ReadEmailParams(
        email=email,
        password=password,
        domain=domain,
        mailbox=mailbox,
        criteria=criteria,
        last=last,
        id_key=id_key,
        seen=seen,
        with_payload=with_payload,
        folder=folder
    )

    if host is None and port is None:
        # Receiving the server host and port
        host, port = get_server(domain=params.domain, server='imap')

    # Set up a connection with the SMTP server
    with imaplib.IMAP4_SSL(host, port) as server:
        logger.debug('IMAP session started')
        server.login(params.email, params.password)
        logger.debug('Authorization completed')
        server.select(params.mailbox)
        # Get emails
        emails = get_emails(
            server=server,
            criteria=params.criteria,
            last=params.last,
            id_key=params.id_key,
            seen=params.seen,
            with_payload=params.with_payload,
            folder=params.folder
        )
        # End IMAP session and close connection
        logger.debug('IMAP session ended')
    return emails
