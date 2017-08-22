.. start-no-pypi

.. image:: https://travis-ci.org/LabD/python-mocksftp.svg?branch=master
    :target: https://travis-ci.org/LabD/python-mocksftp

.. image:: http://codecov.io/github/LabD/python-mocksftp/coverage.svg?branch=master
    :target: http://codecov.io/github/LabD/python-mocksftp?branch=master

.. image:: https://img.shields.io/pypi/v/mocksftp.svg
    :target: https://pypi.python.org/pypi/mocksftp/

.. end-no-pypi

mocksftp - Easily test your sftp client code 
============================================

In-process SFTP server for testing your SFTP related client code.


Usage example
=============

For pytest, use the ``sftp_server`` and ``sftp_client`` fixtures:

.. code-block:: python

    from contextlib import closing
    import py.path


    def test_open_file(sftp_server, sftp_client):
        # Write directly in the server root.
        root_path = py.path.local(sftp_server.root)
        root_path.join('file.txt').write('content')

        # Access the folder via the client
        sftp = sftp_client.open_sftp()
        assert sftp.listdir('.') == ['file.txt']

        with closing(sftp.open('file.txt', 'r')) as data:
            assert data.read() == b'content'


History
=======

This project was started as a fork of https://github.com/carletes/mock-ssh-server
created by Carlos Valiente.

The SSH related code was removed to focus solely on the SFTP protocol.


Alternatives
============

* https://github.com/ulope/pytest-sftpserver
* https://github.com/rspivak/sftpserver
