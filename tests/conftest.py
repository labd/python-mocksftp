import threading

from pytest import fixture

from mocksftp.pytest_plugin import *  # noqa


@fixture
def assert_num_threads():
    yield
    assert threading.active_count() == 1, threading.enumerate()
