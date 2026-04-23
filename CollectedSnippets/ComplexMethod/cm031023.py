def test_config_set_sys_flag(self):
        # Test PyConfig_Set() with sys.flags
        config_get = _testcapi.config_get
        config_set = _testcapi.config_set

        # mutable configuration option mapped to sys.flags
        class unsigned_int(int):
            pass

        def expect_int(value):
            value = int(value)
            return (value, value)

        def expect_bool(value):
            value = int(bool(value))
            return (value, value)

        def expect_bool_not(value):
            value = bool(value)
            return (int(value), int(not value))

        for name, sys_flag, option_type, expect_func in (
            # (some flags cannot be set, see comments below.)
            ('parser_debug', 'debug', bool, expect_bool),
            ('inspect', 'inspect', bool, expect_bool),
            ('interactive', 'interactive', bool, expect_bool),
            ('optimization_level', 'optimize', unsigned_int, expect_int),
            ('write_bytecode', 'dont_write_bytecode', bool, expect_bool_not),
            # user_site_directory
            # site_import
            ('use_environment', 'ignore_environment', bool, expect_bool_not),
            ('verbose', 'verbose', unsigned_int, expect_int),
            ('bytes_warning', 'bytes_warning', unsigned_int, expect_int),
            ('quiet', 'quiet', bool, expect_bool),
            # hash_randomization
            # isolated
            # dev_mode
            # utf8_mode
            # warn_default_encoding
            # safe_path
            ('int_max_str_digits', 'int_max_str_digits', unsigned_int, expect_int),
            # gil
        ):
            if name == "int_max_str_digits":
                new_values = (0, 5_000, 999_999)
                invalid_values = (-1, 40)  # value must 0 or >= 4300
                invalid_types = (1.0, "abc")
            elif option_type == int:
                new_values = (False, True, 0, 1, 5, -5)
                invalid_values = ()
                invalid_types = (1.0, "abc")
            else:
                new_values = (False, True, 0, 1, 5)
                invalid_values = (-5,)
                invalid_types = (1.0, "abc")

            with self.subTest(name=name):
                old_value = config_get(name)
                try:
                    for value in new_values:
                        expected, expect_flag = expect_func(value)

                        config_set(name, value)
                        self.assertEqual(config_get(name), expected)
                        self.assertEqual(getattr(sys.flags, sys_flag), expect_flag)
                        if name == "write_bytecode":
                            self.assertEqual(getattr(sys, "dont_write_bytecode"),
                                             expect_flag)
                        if name == "int_max_str_digits":
                            self.assertEqual(sys.get_int_max_str_digits(),
                                             expect_flag)

                    for value in invalid_values:
                        with self.assertRaises(ValueError):
                            config_set(name, value)

                    for value in invalid_types:
                        with self.assertRaises(TypeError):
                            config_set(name, value)
                finally:
                    config_set(name, old_value)