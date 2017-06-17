import time
import os
import tempfile
import threading

import py.path
from pytest import fixture, raises


def files_equal(fname1, fname2):
    if os.stat(fname1).st_size == os.stat(fname2).st_size:
        with open(fname1, "rb") as f1, open(fname2, "rb") as f2:
            if f1.read() == f2.read():
                return True


def test_sftp_concurrent_connections(assert_num_threads, server):
    def connect():
        with server.client('sample-user') as client:
            sftp = client.open_sftp()
            for i in range(0, 3):
                assert sftp.listdir() == []
                time.sleep(0.2)
            sftp.close()
        time.sleep(0.1)

    threads = []
    for i in range(0, 5):
        thread = threading.Thread(
            target=connect, daemon=True, name='test-thread-%d' % i)
        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    time.sleep(0.1)


def test_sftp_session(server):
    for uid in server.users:
        target_dir = tempfile.mkdtemp()
        target_fname = os.path.join(target_dir, "foo")
        assert not os.access(target_fname, os.F_OK)

        with server.client(uid) as c:
            sftp = c.open_sftp()
            sftp.put(__file__, target_fname, confirm=True)
            assert files_equal(target_fname, __file__)

            second_copy = os.path.join(target_dir, "bar")
            assert not os.access(second_copy, os.F_OK)
            sftp.get(target_fname, second_copy)
            assert files_equal(target_fname, second_copy)


@fixture(params=[("chmod", "/", 0o755),
                 ("chown", "/", 0, 0),
                 ("lstat", "/"),
                 ("readlink", "/etc"),
                 ("remove", "/etc/passwd"),
                 ("rename", "/tmp/foo", "/tmp/bar"),
                 ("symlink", "/tmp/foo", "/tmp/bar"),
                 ("truncate", "/etc/passwd", 0),
                 ("unlink", "/etc/passwd"),
                 ("utime", "/", (0, 0))])
def unsupported_call(request):
    return request.param


def test_sftp_unsupported_calls(server, unsupported_call):
    for uid in server.users:
        with server.client(uid) as c:
            meth, args = unsupported_call[0], unsupported_call[1:]
            sftp = c.open_sftp()
            with raises(IOError) as exc:
                getattr(sftp, meth)(*args)
            assert str(exc.value) == "Operation unsupported"


def test_sftp_list_files(server, client):
    sftp = client.open_sftp()
    assert sftp.listdir('.') == []

    with open(os.path.join(server.root, 'dummy.txt'), 'w') as fh:
        fh.write('dummy-content')

    assert sftp.listdir('.') == ['dummy.txt']


def test_sftp_open_file(server, client):
    root_path = py.path.local(server.root)
    root_path.join('file.txt').write('content')

    sftp = client.open_sftp()
    assert sftp.listdir('.') == ['file.txt']

    data = sftp.open('file.txt', 'r')
    assert data.read() == b'content'


def test_sftp_mkdir(server, client):
    root_path = py.path.local(server.root)

    sftp = client.open_sftp()
    assert sftp.listdir('.') == []
    sftp.mkdir('the-dir')
    assert sftp.listdir('.') == ['the-dir']

    root_path.listdir() == ['the-dir']


def test_sftp_rmdir(server, client):
    root_path = py.path.local(server.root)
    root_path.join('the-dir').mkdir()

    sftp = client.open_sftp()
    assert sftp.listdir('.') == ['the-dir']

    sftp.rmdir('the-dir')
    assert sftp.listdir('.') == []
