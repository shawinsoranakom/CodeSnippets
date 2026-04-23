def test_init_is_python_build_with_home(self):
        # Test _Py_path_config._is_python_build configuration (gh-91985)
        config = self._get_expected_config()
        paths = config['config']['module_search_paths']
        paths_str = os.path.pathsep.join(paths)

        for path in paths:
            if not os.path.isdir(path):
                continue
            if os.path.exists(os.path.join(path, 'os.py')):
                home = os.path.dirname(path)
                break
        else:
            self.fail(f"Unable to find home in {paths!r}")

        prefix = exec_prefix = home
        if MS_WINDOWS:
            stdlib = os.path.join(home, "Lib")
            # Because we are specifying 'home', module search paths
            # are fairly static
            expected_paths = [paths[0], os.path.join(home, 'DLLs'), stdlib]
        else:
            version = f'{sys.version_info.major}.{sys.version_info.minor}'
            stdlib = os.path.join(home, sys.platlibdir, f'python{version}{ABI_THREAD}')
            expected_paths = self.module_search_paths(prefix=home, exec_prefix=home)

        config = {
            'home': home,
            'module_search_paths': expected_paths,
            'prefix': prefix,
            'base_prefix': prefix,
            'exec_prefix': exec_prefix,
            'base_exec_prefix': exec_prefix,
            'pythonpath_env': paths_str,
            'stdlib_dir': stdlib,  # Only correct on _is_python_build==0!
        }
        # The code above is taken from test_init_setpythonhome()
        env = {'TESTHOME': home, 'PYTHONPATH': paths_str}

        env['NEGATIVE_ISPYTHONBUILD'] = '1'
        config['_is_python_build'] = 0
        # This configuration doesn't set a valid stdlibdir/plststdlibdir because
        # with _is_python_build=0 getpath doesn't check for the build directory
        # landmarks in PYTHONHOME/Py_SetPythonHome.
        # getpath correctly shows a warning, which messes up check_all_configs,
        # so we need to ignore stderr.
        self.check_all_configs("test_init_is_python_build", config,
                               api=API_COMPAT, env=env, ignore_stderr=True)

        # config['stdlib_dir'] = os.path.join(home, 'Lib')
        # FIXME: This test does not check if stdlib_dir is calculated correctly.
        #        test_init_is_python_build runs the initialization twice,
        #        setting stdlib_dir in _Py_path_config on the first run, which
        #        then overrides the stdlib_dir calculation (as of GH-108730).

        env['NEGATIVE_ISPYTHONBUILD'] = '0'
        config['_is_python_build'] = 1
        exedir = os.path.dirname(sys.executable)
        with open(os.path.join(exedir, 'pybuilddir.txt'), encoding='utf8') as f:
            expected_paths[1 if MS_WINDOWS else 2] = os.path.normpath(
                os.path.join(exedir, f'{f.read()}\n$'.splitlines()[0]))
        if not MS_WINDOWS:
            # PREFIX (default) is set when running in build directory
            prefix = exec_prefix = sys.prefix
            # stdlib calculation (/Lib) is not yet supported
            expected_paths[0] = self.module_search_paths(prefix=prefix)[0]
            config.update(prefix=prefix, base_prefix=prefix,
                          exec_prefix=exec_prefix, base_exec_prefix=exec_prefix)
        # This also shows the bad stdlib warning, getpath is run twice. The
        # first time with _is_python_build=0, which results in the warning just
        # as explained above. However, the second time a valid standard library
        # should be found, but the stdlib_dir is cached in _Py_path_config from
        # the first run, which ovewrites it, so it also shows the warning.
        # Also ignore stderr.
        self.check_all_configs("test_init_is_python_build", config,
                               api=API_COMPAT, env=env, ignore_stderr=True)