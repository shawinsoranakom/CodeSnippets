def get_expected_config(self, expected_preconfig, expected,
                            env, api, modify_path_cb=None):
        configs = self._get_expected_config()

        pre_config = configs['pre_config']
        for key, value in expected_preconfig.items():
            if value is self.GET_DEFAULT_CONFIG:
                expected_preconfig[key] = pre_config[key]

        if not expected_preconfig['configure_locale'] or api == API_COMPAT:
            # there is no easy way to get the locale encoding before
            # setlocale(LC_CTYPE, "") is called: don't test encodings
            for key in ('filesystem_encoding', 'filesystem_errors',
                        'stdio_encoding', 'stdio_errors'):
                expected[key] = self.IGNORE_CONFIG

        if expected_preconfig['utf8_mode'] == 1:
            if expected['filesystem_encoding'] is self.GET_DEFAULT_CONFIG:
                expected['filesystem_encoding'] = 'utf-8'
            if expected['filesystem_errors'] is self.GET_DEFAULT_CONFIG:
                expected['filesystem_errors'] = self.UTF8_MODE_ERRORS
            if expected['stdio_encoding'] is self.GET_DEFAULT_CONFIG:
                expected['stdio_encoding'] = 'utf-8'
            if expected['stdio_errors'] is self.GET_DEFAULT_CONFIG:
                expected['stdio_errors'] = 'surrogateescape'

        if MS_WINDOWS:
            default_executable = self.test_exe
        elif expected['program_name'] is not self.GET_DEFAULT_CONFIG:
            default_executable = os.path.abspath(expected['program_name'])
        else:
            default_executable = os.path.join(os.getcwd(), '_testembed')
        if expected['executable'] is self.GET_DEFAULT_CONFIG:
            expected['executable'] = default_executable
        if expected['base_executable'] is self.GET_DEFAULT_CONFIG:
            expected['base_executable'] = default_executable
        if expected['program_name'] is self.GET_DEFAULT_CONFIG:
            expected['program_name'] = './_testembed'

        config = configs['config']
        for key, value in expected.items():
            if value is self.GET_DEFAULT_CONFIG:
                expected[key] = config[key]

        if expected['module_search_paths'] is not self.IGNORE_CONFIG:
            pythonpath_env = expected['pythonpath_env']
            if pythonpath_env is not None:
                paths = pythonpath_env.split(os.path.pathsep)
                expected['module_search_paths'] = [*paths, *expected['module_search_paths']]
            if modify_path_cb is not None:
                expected['module_search_paths'] = expected['module_search_paths'].copy()
                modify_path_cb(expected['module_search_paths'])

        for key in self.COPY_PRE_CONFIG:
            if key not in expected_preconfig:
                expected_preconfig[key] = expected[key]