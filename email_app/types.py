import re

from typing import Optional
from pydantic import (
    BaseModel, Extra, FilePath, DirectoryPath, validator, root_validator
)


def valid_email(email: str) -> str:
    """Check email-address."""
    pattern = r'^[\w\.\_\-]+\@[\w]+\.[a-z]{1,5}$'
    if not re.match(pattern, email):
        raise ValueError('Invalid email')
    return email


class Email(BaseModel):
    email: str

    _valid_email = validator('email', allow_reuse=True)(valid_email)

    password: str
    domain: Optional[str] = None

    @validator('domain', always=True)
    def set_domain(cls, v, values):
        if 'email' in values:
            return v or values['email'].split('@')[-1].split('.')[0]

    class Config:
        extra = Extra.forbid
        validate_assignment = True


class SendEmailParams(Email):
    recievers: list[str]

    _valid_contacts = validator(
        'recievers', allow_reuse=True, each_item=True
    )(valid_email)

    subject: Optional[str] = None
    message_text: Optional[str] = None
    message_template: Optional[FilePath] = None
    template_kwargs: Optional[dict] = None

    @root_validator
    def check_message(cls, values):
        text = values.get('message_text')
        template = values.get('message_template')
        kwargs = values.get('template_kwargs')
        error = (
            "One of 'message_text' and 'message_template' must be defined. "
            "If 'message_template' is defined then 'template_kwargs' "
            "must be defined too"
        )
        if text is None:
            if template is None and kwargs is None:
                return values
            elif template is not None and kwargs is not None:
                return values
            else:
                raise ValueError(error)
        elif template is None and kwargs is None:
            return values
        else:
            raise ValueError(error)

    attachments: Optional[list[FilePath]] = []


class ReadEmailParams(Email):
    mailbox: str = 'INBOX'
    criteria: str = 'UNSEEN'
    last: Optional[int] = None
    id_key: Optional[str] = None
    seen: Optional[bool] = None
    with_payload: Optional[bool] = None
    folder: Optional[DirectoryPath] = None
