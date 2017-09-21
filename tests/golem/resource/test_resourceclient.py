import time
import types
import twisted
from twisted.internet.defer import Deferred
import unittest
import unittest.mock as mock
import uuid

from golem.tools.testwithreactor import TestWithReactor
from golem.resource.client import ClientHandler, ClientCommands, ClientError, \
    ClientOptions, ClientConfig
from golem.core.async import AsyncRequest, async_run


class MockClientHandler(ClientHandler):
    def __init__(self, commands_class, config):
        super(MockClientHandler, self).__init__(commands_class, config)

    def command_failed(self, exc, cmd, obj_id):
        pass

    def new_client(self):
        return mock.Mock()


class MockClientConfig(ClientConfig):
    def __init__(self, max_concurrent_downloads=3, max_retries=8, timeout=None):
        super(MockClientConfig, self).__init__(max_concurrent_downloads, max_retries, timeout)


class TestClientHandler(unittest.TestCase):

    def test_can_retry(self):
        valid_exceptions = ClientHandler.timeout_exceptions
        config = MockClientConfig()
        handler = MockClientHandler(ClientCommands, config)
        value_exc = valid_exceptions[0]()

        for exc_class in valid_exceptions:
            try:
                exc = exc_class(value_exc)
            except:
                exc = exc_class.__new__(exc_class)

            assert handler._can_retry(exc, ClientCommands.get, str(uuid.uuid4()))
        assert not handler._can_retry(Exception(value_exc), ClientCommands.get, str(uuid.uuid4()))

        obj_id = str(uuid.uuid4())
        exc = valid_exceptions[0]()

        for i in range(0, config.max_retries):
            can_retry = handler._can_retry(exc, ClientCommands.get, obj_id)
            assert can_retry
        assert not handler._can_retry(exc, ClientCommands.get, obj_id)

    def test_exception_type(self):

        valid_exceptions = ClientHandler.timeout_exceptions
        exc = valid_exceptions[0]()
        failure_exc = twisted.python.failure.Failure(exc_value=exc)

        def is_class(object):
            return isinstance(object, type)

        assert is_class(ClientHandler._exception_type(failure_exc))
        assert is_class(ClientHandler._exception_type(exc))


class TestClientOptions(unittest.TestCase):

    def test_get(self):
        option = 'test_option'

        options = ClientOptions('valid_id', 'valid_version', {})
        options.options[option] = True

        with self.assertRaises(ClientError):
            options.get('valid_id', 'invalid_version', option)
        with self.assertRaises(ClientError):
            options.get('invalid_id', 'valid_version', option)

        assert options.get('valid_id', 'valid_version', option)


class TestAsyncRequest(TestWithReactor):

    def test_callbacks(self):
        done = [False]

        method = mock.Mock()
        req = AsyncRequest(method)

        def success(*_):
            done[0] = True

        def error(*_):
            done[0] = True

        done[0] = False
        method.called = False
        async_run(req, success, error)
        time.sleep(1)

        assert method.called

        done[0] = False
        method.called = False
        async_run(req)
        time.sleep(1)

        assert method.called
