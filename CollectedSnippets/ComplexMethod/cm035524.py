def test_complex_environment_scenario(self):
        """Test a complex scenario with many environment variables."""
        env_vars = {
            'OH_AGENT_SERVER_ENV': '{"APP_NAME": "MyApp", "APP_VERSION": "1.2.3", "APP_ENV": "production", "DB_HOST": "localhost", "DB_PORT": "5432", "DB_NAME": "myapp_db", "FEATURE_X": "enabled", "FEATURE_Y": "disabled", "LOG_JSON": "false", "PYTHONUNBUFFERED": "0"}',
            # Non-matching variables (should be ignored)
            'OTHER_VAR': 'ignored',
            'OH_OTHER_PREFIX_VAR': 'also_ignored',
        }

        with patch.dict(os.environ, env_vars, clear=True):
            # Test with Docker specs as representative
            specs = get_default_docker_sandbox_specs()
            spec = specs[0]

            # Custom variables should be present
            assert spec.initial_env['APP_NAME'] == 'MyApp'
            assert spec.initial_env['APP_VERSION'] == '1.2.3'
            assert spec.initial_env['APP_ENV'] == 'production'
            assert spec.initial_env['DB_HOST'] == 'localhost'
            assert spec.initial_env['DB_PORT'] == '5432'
            assert spec.initial_env['DB_NAME'] == 'myapp_db'
            assert spec.initial_env['FEATURE_X'] == 'enabled'
            assert spec.initial_env['FEATURE_Y'] == 'disabled'

            # Overridden defaults should have new values
            assert spec.initial_env['LOG_JSON'] == 'false'
            assert spec.initial_env['PYTHONUNBUFFERED'] == '0'

            # Non-matching variables should not be present
            assert 'OTHER_VAR' not in spec.initial_env
            assert 'OH_OTHER_PREFIX_VAR' not in spec.initial_env

            # Original defaults that weren't overridden should still be present
            assert 'OPENVSCODE_SERVER_ROOT' in spec.initial_env
            assert 'OH_ENABLE_VNC' in spec.initial_env