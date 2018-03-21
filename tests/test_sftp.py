import os
import stat
import threading
import time

import errno
import py.path
from paramiko import SFTPAttributes
from pytest import fixture, raises


@fixture
def root_path(sftp_server):
    return py.path.local(sftp_server.root)


def files_equal(fname1, fname2):
    if os.stat(fname1).st_size == os.stat(fname2).st_size:
        with open(fname1, "rb") as f1, open(fname2, "rb") as f2:
            if f1.read() == f2.read():
                return True


def test_sftp_concurrent_connections(assert_num_threads, sftp_server):
    def connect():
        with sftp_server.client('sample-user') as client:
            sftp = client.open_sftp()
            for i in range(0, 3):
                assert sftp.listdir() == []
                time.sleep(0.2)
            sftp.close()
        time.sleep(0.1)

    threads = []
    for i in range(0, 5):
        thread = threading.Thread(target=connect, name='test-thread-%d' % i)
        thread.setDaemon(True)
        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    time.sleep(0.1)


def test_sftp_session(root_path, sftp_server):
    for uid in sftp_server.users:
        target_fname = str(root_path.join('foo.py'))
        assert not os.access(target_fname, os.F_OK)

        with sftp_server.client(uid) as c:
            sftp = c.open_sftp()
            sftp.put(__file__, "foo.py", confirm=True)
            assert files_equal(target_fname, __file__)

            second_copy = str(root_path.join('bar.py'))
            assert not os.access(second_copy, os.F_OK)
            sftp.get("foo.py", second_copy)
            assert files_equal(target_fname, second_copy)


def test_sftp_list_files(root_path, sftp_client):
    sftp = sftp_client.open_sftp()
    assert sftp.listdir('.') == []

    root_path.join('dummy.txt').write('dummy-content')
    root_path.join('subdir/foobar.txt').write('dummy2', ensure=True)
    assert sorted(sftp.listdir('.')) == ['dummy.txt', 'subdir']
    assert sftp.listdir('subdir') == ['foobar.txt']


def test_sftp_open_file(root_path, sftp_client):
    root_path.join('file.txt').write('content')

    sftp = sftp_client.open_sftp()
    assert sftp.listdir('.') == ['file.txt']

    data = sftp.open('file.txt', 'r')
    assert data.read() == b'content'


def test_sftp_mkdir(root_path, sftp_client):
    sftp = sftp_client.open_sftp()
    assert sftp.listdir('.') == []
    sftp.mkdir('the-dir')
    assert sftp.listdir('.') == ['the-dir']

    files = [f.basename for f in root_path.listdir()]
    assert files == ['the-dir']


def test_sftp_rmdir(root_path, sftp_client):
    root_path.join('the-dir').mkdir()

    sftp = sftp_client.open_sftp()
    assert sftp.listdir('.') == ['the-dir']

    sftp.rmdir('the-dir')
    assert sftp.listdir('.') == []


def test_sftp_stat(root_path, sftp_client):
    root_path.join('file.txt').write('content')

    sftp = sftp_client.open_sftp()
    statobj = sftp.lstat('file.txt')  # type: SFTPAttributes

    assert statobj.st_size == 7
    assert stat.S_IMODE(statobj.st_mode) == 0o644
    assert stat.S_IFMT(statobj.st_mode) == stat.S_IFREG  # regular file


def test_sftp_lstat(root_path, sftp_client):
    root_path.join('file.txt').write('content')
    root_path.join('symlink.txt').mksymlinkto('file.txt')

    sftp = sftp_client.open_sftp()
    statobj = sftp.lstat('symlink.txt')  # type: SFTPAttributes

    assert statobj.st_size == 8  # symlink size!
    assert stat.S_IFMT(statobj.st_mode) == stat.S_IFLNK  # symlink

    sftp = sftp_client.open_sftp()
    statobj = sftp.stat('symlink.txt')  # type: SFTPAttributes

    # Apply default umask in testing modes,
    # in case it's not set (e.g. docker container)
    assert statobj.st_size == 7
    assert stat.S_IMODE(statobj.st_mode) & ~0o022 == 0o644
    assert stat.S_IFMT(statobj.st_mode) == stat.S_IFREG  # regular file


def test_sftp_readlink(root_path, sftp_client):
    root_path.join('file.txt').write('content')
    root_path.join('symlink.txt').mksymlinkto('file.txt')

    sftp = sftp_client.open_sftp()
    assert sftp.readlink('symlink.txt') == 'file.txt'


def test_sftp_rename(root_path, sftp_client):
    root_path.join('file.txt').write('content')

    sftp = sftp_client.open_sftp()
    sftp.rename('file.txt', 'new.txt')

    files = [f.basename for f in root_path.listdir()]
    assert files == ['new.txt']


def test_sftp_remove_file(root_path, sftp_client):
    root_path.join('file.txt').write('content')

    sftp = sftp_client.open_sftp()
    sftp.remove('file.txt')

    assert not root_path.join('file.txt').check()
    assert len(root_path.listdir()) == 0


def test_sftp_remove_folder(root_path, sftp_client):
    root_path.join('subdir').mkdir()

    sftp = sftp_client.open_sftp()
    sftp.remove('subdir')

    assert not root_path.join('subdir').check()
    assert len(root_path.listdir()) == 0


def test_sftp_symlink(root_path, sftp_client):
    root_path.join('file.txt').write('content')

    sftp = sftp_client.open_sftp()
    sftp.symlink('file.txt', 'link.txt')

    assert root_path.join('link.txt').readlink() == 'file.txt'


def test_sftp_chmod(root_path, sftp_client):
    file = root_path.join('file.txt')
    file.write('content')

    sftp = sftp_client.open_sftp()
    sftp.chmod('file.txt', 0o647)
    assert file.stat().mode == 0o100647


def test_sftp_chown(root_path, sftp_client):
    file = root_path.join('file.txt')
    file.write('content')
    st = os.stat(str(file))

    sftp = sftp_client.open_sftp()
    sftp.chown('file.txt', st.st_uid, st.st_gid)


def test_sftp_truncate(root_path, sftp_client):
    file = root_path.join('file.txt')
    file.write('content')
    sftp = sftp_client.open_sftp()
    sftp.truncate('file.txt', 1)
    assert file.read() == 'c'


def test_sftp_utime(root_path, sftp_client):
    file = root_path.join('file.txt')
    file.write('content')

    sftp = sftp_client.open_sftp()
    sftp.utime('file.txt', (10, 0))

    stat = file.stat()
    assert stat.atime == 10
    assert stat.mtime == 0


def test_sftp_symlink_block_outside(sftp_client):
    sftp = sftp_client.open_sftp()

    with raises(IOError) as exception_info:
        sftp.symlink(
            '../../../../../../../../../../../../../etc/passwd',
            'link.txt'
        )

    assert exception_info.value.errno == errno.EACCES


def test_sftp_block_outside_root(sftp_client):
    sftp = sftp_client.open_sftp()

    with raises(IOError) as exception_info:
        assert sftp.listdir('..')
    assert exception_info.value.errno == errno.EACCES

    with raises(IOError) as exception_info:
        data = sftp.open('../file.txt', 'r')
    assert exception_info.value.errno == errno.EACCES
