from pytest import fixture

from mocksftp import keys
from mocksftp.server import Server


@fixture
def sftp_server(tmpdir):
    root = tmpdir.join('sftp-root').mkdir().strpath
    users = {
        'sample-user': {
            'key': keys.SAMPLE_USER_PRIVATE_KEY,
            'passphrase': None,
        }
    }
    with Server(users, root=root) as s:
        yield s


@fixture
def sftp_client(sftp_server):
    with sftp_server.client('sample-user') as c:
        yield c
