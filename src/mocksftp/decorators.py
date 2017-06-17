import logging

import paramiko

logger = logging.getLogger(__name__)


def returns_sftp_error(func):

    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OSError as err:
            logger.debug(
                "Error calling %s(%s, %s): %s",
                func, args, kwargs, err, exc_info=True)
            return paramiko.SFTPServer.convert_errno(err.errno)
        except Exception as err:
            logger.debug(
                "Error calling %s(%s, %s): %s",
                func, args, kwargs, err, exc_info=True)
            return paramiko.SFTP_FAILURE

    return wrapped
