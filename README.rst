mocksftp - Easily test your sftp client code
============================================

.. image:: https://img.shields.io/pypi/v/mocksftp
    :target: https://pypi.org/project/mocksftp/
    :alt: PyPI

.. image:: https://github.com/labd/python-mocksftp/actions/workflows/python-tests.yml/badge.svg
    :target: https://github.com/labd/python-mocksftp/actions/workflows/python-tests.yml
    :alt: Python Tests

mocksftp runs a real SFTP server in-process, on a background thread, backed by
a local directory. You can test code that talks SFTP (through `paramiko`_ or
any other client) against an actual server, without mocking the client and
without Docker or a running ``sshd``. It ships as a pytest plugin with ready-made
fixtures, and you can also use the server on its own as a context manager.

.. _paramiko: https://www.paramiko.org/


Installation
============

.. code-block:: console

    pip install mocksftp

or with uv, as a development dependency:

.. code-block:: console

    uv add --dev mocksftp


Requirements
============

* Python 3.11 or newer (CI tests 3.11 to 3.14)
* `paramiko`_ (installed automatically)
* pytest, if you want to use the fixtures


Usage
=====

pytest fixtures
---------------

The package registers a pytest plugin through the ``pytest11`` entry point,
so once it is installed the fixtures work without further setup:

``sftp_server``
    A running ``mocksftp.server.Server``. Its root is a fresh ``sftp-root``
    directory inside pytest's ``tmpdir``. It has one user, ``sample-user``,
    who authenticates with the RSA key that ships with the package.

``sftp_client``
    A connected ``paramiko.SSHClient`` logged in as ``sample-user``.

.. code-block:: python

    from pathlib import Path


    def test_open_file(sftp_server, sftp_client):
        # Write directly in the server root.
        Path(sftp_server.root, "file.txt").write_text("content")

        # Access the file via the client.
        sftp = sftp_client.open_sftp()
        assert sftp.listdir(".") == ["file.txt"]

        with sftp.open("file.txt", "r") as fh:
            assert fh.read() == b"content"


    def test_upload(sftp_server, sftp_client):
        sftp = sftp_client.open_sftp()
        sftp.mkdir("incoming")
        with sftp.open("incoming/report.csv", "w") as fh:
            fh.write("id,name\n")

        assert Path(sftp_server.root, "incoming", "report.csv").read_text() == "id,name\n"

To point your own code at the server, use ``sftp_server.host`` (always
``127.0.0.1``) and ``sftp_server.port`` (a random free port picked at start).

Using the server directly
-------------------------

Without pytest, start a ``Server`` as a context manager. Users are a mapping of
username to an RSA private key file and its passphrase. The server only accepts
public key authentication, and only RSA keys.

.. code-block:: python

    import tempfile

    from mocksftp import keys
    from mocksftp.server import Server

    users = {
        "sample-user": {
            "key": keys.SAMPLE_USER_PRIVATE_KEY,
            "passphrase": None,
        }
    }

    with tempfile.TemporaryDirectory() as root:
        with Server(users, root=root) as server:
            with server.client("sample-user") as client:
                sftp = client.open_sftp()
                sftp.mkdir("data")
                print(sftp.listdir("."))  # ['data']

Use ``server.add_user(uid, private_key_path, passphrase=None)`` to add users
after creating the server. ``server.client(uid)`` is a context manager that
yields a ``paramiko.SSHClient`` that is connected and trusts the server's
host key.

Supported operations
--------------------

Operations are handled on the local filesystem under the server root. Paths
that resolve outside the root are rejected. Supported: ``listdir``/``listdir_attr``,
``open``, ``mkdir``, ``rmdir``, ``remove``, ``stat``,
``lstat``, ``rename``, ``posix_rename``, ``chmod``, ``chown``, ``utime``,
``truncate``, ``symlink`` and ``readlink``.


Configuration
=============

There is no configuration through environment variables. The bundled keys are
in ``mocksftp.keys``:

* ``keys.SAMPLE_USER_PRIVATE_KEY``: private key for the default ``sample-user``
* ``keys.SERVER_PRIVATE_KEY``: the server's host key

These keys are public and only meant for tests. Do not use them for anything
else.


Development
===========

The project uses `uv`_. The ``Makefile`` wraps the common commands:

.. code-block:: console

    make install    # uv sync
    make test       # uv run pytest
    make coverage   # pytest with coverage report
    make lint       # ruff format --check + ruff check
    make format     # apply ruff fixes and formatting

CI (``.github/workflows/python-tests.yml``) runs ``ruff format --check`` and
``ruff check`` on ``src`` and ``tests``. It then runs
``uv run --frozen coverage run -m pytest`` on Python 3.11 to 3.14.

.. _uv: https://docs.astral.sh/uv/


Release process
===============

Releases are managed with `changie <https://changie.dev>`_:

1. Add a changelog entry to your pull request with ``changie new``.
2. After merging to ``master``, a release pull request is opened (or updated)
   automatically, with the new version and the updated ``CHANGELOG.md``.
3. Merging the release pull request creates the GitHub release, which publishes
   the package to PyPI.


History
=======

This project was started as a fork of https://github.com/carletes/mock-ssh-server
created by Carlos Valiente.

The SSH related code was removed to focus solely on the SFTP protocol.


Alternatives
============

* https://github.com/ulope/pytest-sftpserver
* https://github.com/rspivak/sftpserver


License
=======

MIT, see `LICENSE <https://github.com/labd/python-mocksftp/blob/master/LICENSE>`_.
