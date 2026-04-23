def test_update_from_dict(self):
        for name, vanilla in self.supported.items():
            with self.subTest(f'noop ({name})'):
                expected = vanilla
                overrides = vars(vanilla)
                config = _interpreters.new_config(name, **overrides)
                self.assert_ns_equal(config, expected)

            with self.subTest(f'change all ({name})'):
                overrides = {k: not v for k, v in vars(vanilla).items()}
                for gil in self.gil_supported:
                    if vanilla.gil == gil:
                        continue
                    overrides['gil'] = gil
                    expected = types.SimpleNamespace(**overrides)
                    config = _interpreters.new_config(
                                                            name, **overrides)
                    self.assert_ns_equal(config, expected)

            # Override individual fields.
            for field, old in vars(vanilla).items():
                if field == 'gil':
                    values = [v for v in self.gil_supported if v != old]
                else:
                    values = [not old]
                for val in values:
                    with self.subTest(f'{name}.{field} ({old!r} -> {val!r})'):
                        overrides = {field: val}
                        expected = types.SimpleNamespace(
                            **dict(vars(vanilla), **overrides),
                        )
                        config = _interpreters.new_config(
                                                            name, **overrides)
                        self.assert_ns_equal(config, expected)

        with self.subTest('unsupported field'):
            for name in self.supported:
                with self.assertRaises(ValueError):
                    _interpreters.new_config(name, spam=True)

        # Bad values for bool fields.
        for field, value in vars(self.supported['empty']).items():
            if field == 'gil':
                continue
            assert isinstance(value, bool)
            for value in [1, '', 'spam', 1.0, None, object()]:
                with self.subTest(f'unsupported value ({field}={value!r})'):
                    with self.assertRaises(TypeError):
                        _interpreters.new_config(**{field: value})

        # Bad values for .gil.
        for value in [True, 1, 1.0, None, object()]:
            with self.subTest(f'unsupported value(gil={value!r})'):
                with self.assertRaises(TypeError):
                    _interpreters.new_config(gil=value)
        for value in ['', 'spam']:
            with self.subTest(f'unsupported value (gil={value!r})'):
                with self.assertRaises(ValueError):
                    _interpreters.new_config(gil=value)