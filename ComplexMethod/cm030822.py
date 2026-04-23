def test_builtin_exceptions(self):
        new_names = {
            'BlockingIOError': (3, 3),
            'BrokenPipeError': (3, 3),
            'ChildProcessError': (3, 3),
            'ConnectionError': (3, 3),
            'ConnectionAbortedError': (3, 3),
            'ConnectionRefusedError': (3, 3),
            'ConnectionResetError': (3, 3),
            'FileExistsError': (3, 3),
            'FileNotFoundError': (3, 3),
            'InterruptedError': (3, 3),
            'IsADirectoryError': (3, 3),
            'NotADirectoryError': (3, 3),
            'PermissionError': (3, 3),
            'ProcessLookupError': (3, 3),
            'TimeoutError': (3, 3),
            'RecursionError': (3, 5),
            'StopAsyncIteration': (3, 5),
            'ModuleNotFoundError': (3, 6),
            'EncodingWarning': (3, 10),
            'BaseExceptionGroup': (3, 11),
            'ExceptionGroup': (3, 11),
            '_IncompleteInputError': (3, 13),
            'PythonFinalizationError': (3, 13),
            'ImportCycleError': (3, 15),
        }
        for t in builtins.__dict__.values():
            if isinstance(t, type) and issubclass(t, BaseException):
                if t.__name__ in new_names and self.py_version < new_names[t.__name__]:
                    continue
                for proto in protocols:
                    with self.subTest(name=t.__name__, proto=proto):
                        if self.py_version < (3, 3) and proto < 3:
                            self.skipTest('exception classes are not interoperable with Python < 3.3')
                        s = self.dumps(t, proto)
                        u = self.loads(s)
                        if proto <= 2 and issubclass(t, OSError) and t is not BlockingIOError:
                            self.assertIs(u, OSError)
                        elif proto <= 2 and issubclass(t, ImportError):
                            self.assertIs(u, ImportError)
                        else:
                            self.assertIs(u, t)