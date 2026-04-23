def test_config_get(self):
        # Test PyConfig_Get()
        config_get = _testcapi.config_get
        config_names = _testcapi.config_names

        TEST_VALUE = {
            str: "TEST_MARKER_STR",
            str | None: "TEST_MARKER_OPT_STR",
            list[str]: ("TEST_MARKER_STR_TUPLE",),
            dict[str, str | bool]: {"x": "value", "y": True},
        }

        # read config options and check their type
        options = [
            ("allocator", int, None),
            ("argv", list[str], "argv"),
            ("base_exec_prefix", str | None, "base_exec_prefix"),
            ("base_executable", str | None, "_base_executable"),
            ("base_prefix", str | None, "base_prefix"),
            ("buffered_stdio", bool, None),
            ("bytes_warning", int, None),
            ("check_hash_pycs_mode", str, None),
            ("code_debug_ranges", bool, None),
            ("configure_c_stdio", bool, None),
            ("coerce_c_locale", bool, None),
            ("coerce_c_locale_warn", bool, None),
            ("configure_locale", bool, None),
            ("cpu_count", int, None),
            ("dev_mode", bool, None),
            ("dump_refs", bool, None),
            ("dump_refs_file", str | None, None),
            ("exec_prefix", str | None, "exec_prefix"),
            ("executable", str | None, "executable"),
            ("faulthandler", bool, None),
            ("filesystem_encoding", str, None),
            ("filesystem_errors", str, None),
            ("hash_seed", int, None),
            ("home", str | None, None),
            ("thread_inherit_context", int, None),
            ("context_aware_warnings", int, None),
            ("import_time", int, None),
            ("inspect", bool, None),
            ("install_signal_handlers", bool, None),
            ("int_max_str_digits", int, None),
            ("interactive", bool, None),
            ("isolated", bool, None),
            ("lazy_imports", int, None),
            ("malloc_stats", bool, None),
            ("pymalloc_hugepages", bool, None),
            ("module_search_paths", list[str], "path"),
            ("optimization_level", int, None),
            ("orig_argv", list[str], "orig_argv"),
            ("parser_debug", bool, None),
            ("parse_argv", bool, None),
            ("pathconfig_warnings", bool, None),
            ("perf_profiling", int, None),
            ("platlibdir", str, "platlibdir"),
            ("prefix", str | None, "prefix"),
            ("program_name", str, None),
            ("pycache_prefix", str | None, "pycache_prefix"),
            ("quiet", bool, None),
            ("remote_debug", int, None),
            ("run_command", str | None, None),
            ("run_filename", str | None, None),
            ("run_module", str | None, None),
            ("safe_path", bool, None),
            ("show_ref_count", bool, None),
            ("site_import", bool, None),
            ("skip_source_first_line", bool, None),
            ("stdio_encoding", str, None),
            ("stdio_errors", str, None),
            ("stdlib_dir", str | None, "_stdlib_dir"),
            ("tracemalloc", int, None),
            ("use_environment", bool, None),
            ("use_frozen_modules", bool, None),
            ("use_hash_seed", bool, None),
            ("user_site_directory", bool, None),
            ("utf8_mode", bool, None),
            ("verbose", int, None),
            ("warn_default_encoding", bool, None),
            ("warnoptions", list[str], "warnoptions"),
            ("write_bytecode", bool, None),
            ("xoptions", dict[str, str | bool], "_xoptions"),
        ]
        if support.Py_DEBUG:
            options.append(("run_presite", str | None, None))
        if support.Py_GIL_DISABLED:
            options.append(("enable_gil", int, None))
            options.append(("tlbc_enabled", int, None))
        if support.MS_WINDOWS:
            options.extend((
                ("legacy_windows_stdio", bool, None),
                ("legacy_windows_fs_encoding", bool, None),
            ))
        if Py_STATS:
            options.extend((
                ("_pystats", bool, None),
            ))
        if support.is_apple:
            options.extend((
                ("use_system_logger", bool, None),
            ))

        for name, option_type, sys_attr in options:
            with self.subTest(name=name, option_type=option_type,
                              sys_attr=sys_attr):
                value = config_get(name)
                if isinstance(option_type, types.GenericAlias):
                    self.assertIsInstance(value, option_type.__origin__)
                    if option_type.__origin__ == dict:
                        key_type = option_type.__args__[0]
                        value_type = option_type.__args__[1]
                        for item in value.items():
                            self.assertIsInstance(item[0], key_type)
                            self.assertIsInstance(item[1], value_type)
                    else:
                        item_type = option_type.__args__[0]
                        for item in value:
                            self.assertIsInstance(item, item_type)
                else:
                    self.assertIsInstance(value, option_type)

                if sys_attr is not None:
                    expected = getattr(sys, sys_attr)
                    self.assertEqual(expected, value)

                    override = TEST_VALUE[option_type]
                    with support.swap_attr(sys, sys_attr, override):
                        self.assertEqual(config_get(name), override)

        # check that the test checks all options
        self.assertEqual(sorted(name for name, option_type, sys_attr in options),
                         sorted(config_names()))