def test_new_config(self):
        # This test overlaps with
        # test.test_capi.test_misc.InterpreterConfigTests.

        default = _interpreters.new_config('isolated')
        with self.subTest('no arg'):
            config = _interpreters.new_config()
            self.assert_ns_equal(config, default)
            self.assertIsNot(config, default)

        with self.subTest('default'):
            config1 = _interpreters.new_config('default')
            self.assert_ns_equal(config1, default)
            self.assertIsNot(config1, default)

            config2 = _interpreters.new_config('default')
            self.assert_ns_equal(config2, config1)
            self.assertIsNot(config2, config1)

        for arg in ['', 'default']:
            with self.subTest(f'default ({arg!r})'):
                config = _interpreters.new_config(arg)
                self.assert_ns_equal(config, default)
                self.assertIsNot(config, default)

        supported = {
            'isolated': types.SimpleNamespace(
                use_main_obmalloc=False,
                allow_fork=False,
                allow_exec=False,
                allow_threads=True,
                allow_daemon_threads=False,
                check_multi_interp_extensions=True,
                gil='own',
            ),
            'legacy': types.SimpleNamespace(
                use_main_obmalloc=True,
                allow_fork=True,
                allow_exec=True,
                allow_threads=True,
                allow_daemon_threads=True,
                check_multi_interp_extensions=bool(Py_GIL_DISABLED),
                gil='shared',
            ),
            'empty': types.SimpleNamespace(
                use_main_obmalloc=False,
                allow_fork=False,
                allow_exec=False,
                allow_threads=False,
                allow_daemon_threads=False,
                check_multi_interp_extensions=False,
                gil='default',
            ),
        }
        gil_supported = ['default', 'shared', 'own']

        for name, vanilla in supported.items():
            with self.subTest(f'supported ({name})'):
                expected = vanilla
                config1 = _interpreters.new_config(name)
                self.assert_ns_equal(config1, expected)
                self.assertIsNot(config1, expected)

                config2 = _interpreters.new_config(name)
                self.assert_ns_equal(config2, config1)
                self.assertIsNot(config2, config1)

            with self.subTest(f'noop override ({name})'):
                expected = vanilla
                overrides = vars(vanilla)
                config = _interpreters.new_config(name, **overrides)
                self.assert_ns_equal(config, expected)

            with self.subTest(f'override all ({name})'):
                overrides = {k: not v for k, v in vars(vanilla).items()}
                for gil in gil_supported:
                    if vanilla.gil == gil:
                        continue
                    overrides['gil'] = gil
                    expected = types.SimpleNamespace(**overrides)
                    config = _interpreters.new_config(name, **overrides)
                    self.assert_ns_equal(config, expected)

            # Override individual fields.
            for field, old in vars(vanilla).items():
                if field == 'gil':
                    values = [v for v in gil_supported if v != old]
                else:
                    values = [not old]
                for val in values:
                    with self.subTest(f'{name}.{field} ({old!r} -> {val!r})'):
                        overrides = {field: val}
                        expected = types.SimpleNamespace(
                            **dict(vars(vanilla), **overrides),
                        )
                        config = _interpreters.new_config(name, **overrides)
                        self.assert_ns_equal(config, expected)

        with self.subTest('extra override'):
            with self.assertRaises(ValueError):
                _interpreters.new_config(spam=True)

        # Bad values for bool fields.
        for field, value in vars(supported['empty']).items():
            if field == 'gil':
                continue
            assert isinstance(value, bool)
            for value in [1, '', 'spam', 1.0, None, object()]:
                with self.subTest(f'bad override ({field}={value!r})'):
                    with self.assertRaises(TypeError):
                        _interpreters.new_config(**{field: value})

        # Bad values for .gil.
        for value in [True, 1, 1.0, None, object()]:
            with self.subTest(f'bad override (gil={value!r})'):
                with self.assertRaises(TypeError):
                    _interpreters.new_config(gil=value)
        for value in ['', 'spam']:
            with self.subTest(f'bad override (gil={value!r})'):
                with self.assertRaises(ValueError):
                    _interpreters.new_config(gil=value)