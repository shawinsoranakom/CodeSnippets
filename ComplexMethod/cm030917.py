def test_sysconfigdata_json(self):
        if '_PYTHON_SYSCONFIGDATA_PATH' in os.environ:
            data_dir = os.environ['_PYTHON_SYSCONFIGDATA_PATH']
        elif is_python_build():
            data_dir = os.path.join(_PROJECT_BASE, _get_pybuilddir())
        else:
            data_dir = sys._stdlib_dir

        json_data_path = os.path.join(data_dir, _get_json_data_name())

        with open(json_data_path) as f:
            json_config_vars = json.load(f)

        system_config_vars = get_config_vars()

        # Keys dependent on uncontrollable external context
        ignore_keys = {'userbase'}
        # Keys dependent on Python being run outside the build directrory
        if sysconfig.is_python_build():
            ignore_keys |= {'srcdir'}
        # Keys dependent on the executable location
        if os.path.dirname(sys.executable) != system_config_vars['BINDIR']:
            ignore_keys |= {'projectbase'}
        # Keys dependent on the environment (different inside virtual environments)
        if sys.prefix != sys.base_prefix:
            ignore_keys |= {'prefix', 'exec_prefix', 'base', 'platbase'}
        # Keys dependent on Python being run from the prefix targetted when building (different on relocatable installs)
        if sysconfig._installation_is_relocated():
            ignore_keys |= {'prefix', 'exec_prefix', 'base', 'platbase', 'installed_base', 'installed_platbase', 'srcdir'}

        for key in ignore_keys:
            json_config_vars.pop(key, None)
            system_config_vars.pop(key, None)

        self.assertEqual(system_config_vars, json_config_vars)