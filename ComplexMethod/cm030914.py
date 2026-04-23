def check_all_configs(self, testname, expected_config=None,
                          expected_preconfig=None,
                          modify_path_cb=None,
                          stderr=None, *, api, preconfig_api=None,
                          env=None, ignore_stderr=False, cwd=None):
        new_env = remove_python_envvars()
        if env is not None:
            new_env.update(env)
        env = new_env

        if preconfig_api is None:
            preconfig_api = api
        if preconfig_api == API_ISOLATED:
            default_preconfig = self.PRE_CONFIG_ISOLATED
        elif preconfig_api == API_PYTHON:
            default_preconfig = self.PRE_CONFIG_PYTHON
        else:
            default_preconfig = self.PRE_CONFIG_COMPAT
        if expected_preconfig is None:
            expected_preconfig = {}
        expected_preconfig = dict(default_preconfig, **expected_preconfig)

        if expected_config is None:
            expected_config = {}

        if api == API_PYTHON:
            default_config = self.CONFIG_PYTHON
        elif api == API_ISOLATED:
            default_config = self.CONFIG_ISOLATED
        else:
            default_config = self.CONFIG_COMPAT
        expected_config = dict(default_config, **expected_config)

        self.get_expected_config(expected_preconfig,
                                 expected_config,
                                 env,
                                 api, modify_path_cb)

        out, err = self.run_embedded_interpreter(testname,
                                                 env=env, cwd=cwd)
        if stderr is None and not expected_config['verbose']:
            stderr = ""
        if stderr is not None and not ignore_stderr:
            self.assertEqual(err.rstrip(), stderr)
        try:
            configs = json.loads(out)
        except json.JSONDecodeError:
            self.fail(f"fail to decode stdout: {out!r}")

        self.check_pre_config(configs, expected_preconfig)
        self.check_config(configs, expected_config)
        self.check_global_config(configs)
        return configs