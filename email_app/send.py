from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import os
import mimetypes
from pathlib import Path
import smtplib
import string

from jinja2 import Environment, FileSystemLoader

from .types import SendEmailParams
from .utils import get_server


def create_message(sender: str, reciever: str, subject: str = None):
    """Create a message object.

    sender      email sender
    reciever    email reciever or recievers (via ', ')

    Additional parameters:
    subject     email subject;

    return      email.mime.multipart.MIMEMultipart object to which you can
                attach text, files and send.
    """
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = reciever
    if subject:
        message['Subject'] = subject
    return message


def read_txt_template(filepath: Path):
    """Read message template txt-file.

    filepath    template file path;

    return      string.Template object.
    """
    logger = logging.getLogger(__name__)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.debug('Template file read')
        return string.Template(content)
    except FileNotFoundError:
        logger.error(f'Template file ({filepath}) not exists')


def read_html_template(filepath: Path):
    """Read message template html-file.

    filepath    template file path;

    return      jinja2.environment.Template object.
    """
    template_path = filepath.split(os.sep)
    template_dir = (
        os.sep.join(template_path[:-1]) if len(template_path) > 1
        else os.path.dirname(__file__)
    )
    loader = FileSystemLoader(template_dir)
    env = Environment(loader=loader)
    template = env.get_template(template_path[-1])
    return template


def create_message_text(template_path: Path, template_kwargs: dict = {}):
    """Create a message content object.

    template_path      template file path (txt or html);
    template_kwargs    dictionary with values for template substitution;

    return             email.mime.text.MIMEText object.
    """
    logger = logging.getLogger(__name__)
    # Definiton the template file type
    file_extention = template_path.split('.')[-1]

    if file_extention == 'txt':
        logger.debug('Template file recognized as txt')
        logger.debug('Reading template file')
        template = read_txt_template(template_path)
        if not template:
            return
        # Substitution of values in the template
        try:
            message_text = template.substitute(template_kwargs)
            logger.debug('Template substituted')
        except KeyError as err:
            error_message = (
                'An error occured during template substitution. '
                f'Could not find value for key {err}'
            )
            logger.error(error_message)
            return
        # Creation of a message content object
        message_text = MIMEText(message_text, 'plain')
        logger.debug('Message text rendered')
        return message_text

    elif file_extention == 'html':
        logger.debug('Template file recognized as html')
        logger.debug('Reading template file')
        template = read_html_template(template_path)
        if not template:
            return
        # Substitution of values in the template
        message_text = template.render(data=template_kwargs)
        # Creation of a message content object
        message_text = MIMEText(message_text, 'html')
        logger.debug('Message text rendered')
        return message_text

    else:
        message = (
            "Unable to read template file. "
            "Extention must be 'txt' or 'html'"
        )
        logger.error(message)
        raise ValueError(message)


def get_attachments(filepaths: list[Path]) -> list:
    """Convert files into email.mime.base.MIMEBase objects
    that can be attached to a message object.

    filepaths    attachment file paths;

    return       list[email.mime.base.MIMEBase object].
    """
    logger = logging.getLogger(__name__)
    # Parsing each file
    attachments = []
    for filepath in filepaths:
        ctype, encoding = mimetypes.guess_type(filepath)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        if maintype == 'text':
            with open(filepath) as fp:
                attachment = MIMEText(fp.read(), _subtype=subtype)
        elif maintype == 'image':
            with open(filepath, 'rb') as fp:
                attachment = MIMEImage(fp.read(), _subtype=subtype)
        elif maintype == 'audio':
            with open(filepath, 'rb') as fp:
                attachment = MIMEAudio(fp.read(), _subtype=subtype)
        else:
            with open(filepath, 'rb') as fp:
                attachment = MIMEBase(maintype, subtype)
                attachment.set_payload(fp.read())
            encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            'attachment',
            filename=os.path.basename(filepath)
        )
        attachments.append(attachment)
        logger.debug(
            'File processed as attachment '
            f'({os.path.basename(filepath)})'
        )
    return attachments


def send_email(
    email: str,
    password: str,
    recievers: list[str],
    domain: str = None,
    subject: str = None,
    message_text: str = None,
    message_template: Path = None,
    template_kwargs: dict = None,
    attachments: list[Path] = None,
    host: str = None,
    port: int = None
):
    """Send email messages. The text of the message can be transmitted
    a string or use a message template. You can attach files to the message.

    email               sender email address;
    password            email app password;
    recievers          email recievers;
    domain              domain of the email service.
                        If None, will be received from email.
                        Examples: google, yandex;

    Additional parameters:
    subject             email subject;
    message_text        message text;
    message_template    template file path (txt or html);
    template_kwargs     dictionary with values for template substitution;
    attachments         attachment file paths;
    host                SMTP-server host;
    port                SMTP-server port.

    return              None.
    """
    logger = logging.getLogger(__name__)
    # Check parameters
    params = SendEmailParams(
        email=email,
        password=password,
        domain=domain,
        recievers=recievers,
        subject=subject,
        message_text=message_text,
        message_template=message_template,
        template_kwargs=template_kwargs,
        attachments=attachments
    )

    if host is None and port is None:
        # Receiving the server host and port
        host, port = get_server(domain=params.domain, server='smtp')

    # Set up a connection with the SMTP server
    # context = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port) as server:
        logger.debug('SMTP session started')
        server.login(params.email, params.password)
        logger.debug('Authorization completed')

        # Create message object
        message_to = ', '.join(params.recievers)
        message = create_message(
            sender=params.email, reciever=message_to, subject=params.subject
        )

        # Process template and add text
        logger.debug('Rendering message text')
        if params.message_text:
            message_text = MIMEText(params.message_text, 'plain')
            message.attach(message_text)
        elif params.message_template:
            message_text = create_message_text(
                template_path=params.message_template,
                template_kwargs=params.template_kwargs
            )
            message.attach(message_text)
        logger.debug('Message text attached')

        # Process and add attachments
        if params.attachments:
            attachments = get_attachments(params.attachments)
            for attachment in attachments:
                message.attach(attachment)
            logger.debug('All files attached')

        # Send message
        server.send_message(message)
        logger.info(
            f'Email message sent from [{params.email}] to [{message_to}]'
        )
        # End SMTP session and close connection
        logger.debug('SMTP session ended')
