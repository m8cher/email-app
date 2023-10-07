import json
import logging
import os


with open(
    os.path.join(os.path.dirname(__file__), 'servers.json'), 'r',
    encoding='utf-8'
) as f:
    SERVERS = json.load(f)


def get_server(domain: str, server: str):
    logger = logging.getLogger(__name__)
    server_dict = SERVERS.get(domain, {}).get(server, {})
    if server_dict:
        logger.debug('Host and port of SMTP server recieved')
        return server_dict['host'], server_dict['port']
    else:
        message = 'Could not receive host and port of SMTP server'
        logger.error(message)
        raise ValueError(message)
