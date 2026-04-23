def test_stateless_func_returns_arg(self):
        interp = interpreters.create()

        for arg in [
            None,
            10,
            'spam!',
            b'spam!',
            (1, 2, 'spam!'),
            memoryview(b'spam!'),
        ]:
            with self.subTest(f'shareable {arg!r}'):
                assert _interpreters.is_shareable(arg)
                res = interp.call(defs.spam_returns_arg, arg)
                self.assertEqual(res, arg)

        for arg in defs.STATELESS_FUNCTIONS:
            with self.subTest(f'stateless func {arg!r}'):
                res = interp.call(defs.spam_returns_arg, arg)
                self.assert_funcs_equal(res, arg)

        for arg in defs.TOP_FUNCTIONS:
            if arg in defs.STATELESS_FUNCTIONS:
                continue
            with self.subTest(f'stateful func {arg!r}'):
                res = interp.call(defs.spam_returns_arg, arg)
                self.assert_funcs_equal(res, arg)
                assert is_pickleable(arg)

        for arg in [
            Ellipsis,
            NotImplemented,
            object(),
            2**1000,
            [1, 2, 3],
            {'a': 1, 'b': 2},
            types.SimpleNamespace(x=42),
            # builtin types
            object,
            type,
            Exception,
            ModuleNotFoundError,
            # builtin exceptions
            Exception('uh-oh!'),
            ModuleNotFoundError('mymodule'),
            # builtin fnctions
            len,
            sys.exit,
            # user classes
            *defs.TOP_CLASSES,
            *(c(*a) for c, a in defs.TOP_CLASSES.items()
              if c not in defs.CLASSES_WITHOUT_EQUALITY),
        ]:
            with self.subTest(f'pickleable {arg!r}'):
                res = interp.call(defs.spam_returns_arg, arg)
                if type(arg) is object:
                    self.assertIs(type(res), object)
                elif isinstance(arg, BaseException):
                    self.assert_exceptions_equal(res, arg)
                else:
                    self.assertEqual(res, arg)
                assert is_pickleable(arg)

        for arg in [
            types.MappingProxyType({}),
            *(f for f in defs.NESTED_FUNCTIONS
              if f not in defs.STATELESS_FUNCTIONS),
        ]:
            with self.subTest(f'unpickleable {arg!r}'):
                assert not _interpreters.is_shareable(arg)
                assert not is_pickleable(arg)
                with self.assertRaises(interpreters.NotShareableError):
                    interp.call(defs.spam_returns_arg, arg)