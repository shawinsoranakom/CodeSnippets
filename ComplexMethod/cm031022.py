def test_config_get_sys_flags(self):
        # Test PyConfig_Get()
        config_get = _testcapi.config_get

        # compare config options with sys.flags
        for flag, name, negate in (
            ("debug", "parser_debug", False),
            ("inspect", "inspect", False),
            ("interactive", "interactive", False),
            ("optimize", "optimization_level", False),
            ("dont_write_bytecode", "write_bytecode", True),
            ("no_user_site", "user_site_directory", True),
            ("no_site", "site_import", True),
            ("ignore_environment", "use_environment", True),
            ("verbose", "verbose", False),
            ("bytes_warning", "bytes_warning", False),
            ("quiet", "quiet", False),
            # "hash_randomization" is tested below
            ("isolated", "isolated", False),
            ("dev_mode", "dev_mode", False),
            ("utf8_mode", "utf8_mode", False),
            ("warn_default_encoding", "warn_default_encoding", False),
            ("safe_path", "safe_path", False),
            ("int_max_str_digits", "int_max_str_digits", False),
            # "gil", "thread_inherit_context" and "context_aware_warnings" are tested below
        ):
            with self.subTest(flag=flag, name=name, negate=negate):
                value = config_get(name)
                if negate:
                    value = not value
                self.assertEqual(getattr(sys.flags, flag), value)

        self.assertEqual(sys.flags.hash_randomization,
                         config_get('use_hash_seed') == 0
                         or config_get('hash_seed') != 0)

        if support.Py_GIL_DISABLED:
            value = config_get('enable_gil')
            expected = (value if value != -1 else None)
            self.assertEqual(sys.flags.gil, expected)

        expected_inherit_context = 1 if support.Py_GIL_DISABLED else 0
        self.assertEqual(sys.flags.thread_inherit_context, expected_inherit_context)

        expected_safe_warnings = 1 if support.Py_GIL_DISABLED else 0
        self.assertEqual(sys.flags.context_aware_warnings, expected_safe_warnings)