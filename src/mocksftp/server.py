import logging
import select
import socket
import threading
import time
from contextlib import contextmanager

import paramiko

from mocksftp import interface, keys

try:
    from queue import Queue
except ImportError:
    from Queue import Queue  # noqa


__all__ = [
    'Server',
]


class Handler(paramiko.ServerInterface):

    log = logging.getLogger(__name__)

    def __init__(self, server):
        self.server = server

    def check_auth_publickey(self, username, key):
        try:
            _, known_public_key = self.server._users[username]
        except KeyError:
            self.log.debug("Unknown user '%s'", username)
            return paramiko.AUTH_FAILED
        if known_public_key == key:
            self.log.debug("Accepting public key for user '%s'", username)
            return paramiko.AUTH_SUCCESSFUL
        self.log.debug("Rejecting public ley for user '%s'", username)
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username):
        return "publickey"


class Server(object):

    host = "127.0.0.1"

    log = logging.getLogger(__name__)

    def __init__(self, users=None, root=None):
        self._event = threading.Event()

        self._socket = None
        self._thread = None
        self._root = root
        self._users = {}
        self._lock = threading.RLock()
        self._transports = []

        users = users or {}
        for uid, credentials in users.items():
            self.add_user(uid, credentials['key'], credentials['passphrase'])

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc_info):
        self.stop()

    def add_user(self, uid, private_key_path, passphrase=None):
        k = paramiko.RSAKey.from_private_key_file(private_key_path, passphrase)
        self._users[uid] = (private_key_path, k)

    def start(self):
        # Initialize the socket before starting the thread. Otherwise there
        # is a good chance for a race condition when resolving the port with
        # the port attribute.
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((self.host, 0))
        self._socket.listen(5)

        self._thread = threading.Thread(target=self._run)
        self._thread.setDaemon(True)
        self._thread.start()

    def stop(self):
        self._event.set()
        self._thread.join()

    def _run(self):

        sock = self._socket
        while sock.fileno() > 0:
            rlist, _, _ = select.select([sock], [], [], 0.050)

            if self._event.is_set():
                break

            if rlist:
                conn, addr = sock.accept()
                self._handle_connection(conn)

        self.log.debug("Stopping server")
        self._event.set()

        # Close the current running transports
        with self._lock:
            for transport in self._transports:
                if transport.active:
                    transport.close()
            self._transports = []

        try:
            self._socket.shutdown(socket.SHUT_RDWR)
            self._socket.close()
        except Exception:
            pass

        self._socket = None
        self._thread = None

    def _handle_connection(self, conn):
        server = Handler(self)

        transport = paramiko.Transport(conn)
        transport.add_server_key(paramiko.RSAKey(filename=keys.SERVER_PRIVATE_KEY))
        transport.set_subsystem_handler(
            'sftp',
            paramiko.SFTPServer,
            root=self._root,
            sftp_si=interface.SFTPServerInterface)

        transport.start_server(server=server)
        with self._lock:
            self._transports.append(transport)

    @contextmanager
    def client(self, uid):
        private_key_path, _ = self._users[uid]
        client = paramiko.SSHClient()

        key = paramiko.RSAKey.from_private_key_file(keys.SERVER_PRIVATE_KEY)
        host_keys = client.get_host_keys()
        host_keys.add(self.host, "ssh-rsa", key)
        host_keys.add("[%s]:%d" % (self.host, self.port), "ssh-rsa", key)

        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        client.connect(
            hostname=self.host,
            port=self.port,
            username=uid,
            key_filename=private_key_path,
            allow_agent=False,
            look_for_keys=False)

        with client:
            yield client
            time.sleep(0.005)

    @property
    def port(self):
        return self._socket.getsockname()[1]

    @property
    def users(self):
        return self._users.keys()

    @property
    def root(self):
        return self._root
