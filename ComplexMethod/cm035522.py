def test_docker_specs_include_agent_server_env(self):
        """Test that Docker sandbox specs include agent server environment variables."""
        env_vars = {
            'OH_AGENT_SERVER_ENV': '{"CUSTOM_VAR": "custom_value", "DEBUG": "true"}',
        }

        with patch.dict(os.environ, env_vars, clear=True):
            specs = get_default_docker_sandbox_specs()

            assert len(specs) == 1
            spec = specs[0]

            # Check that custom environment variables are included
            assert 'CUSTOM_VAR' in spec.initial_env
            assert spec.initial_env['CUSTOM_VAR'] == 'custom_value'
            assert 'DEBUG' in spec.initial_env
            assert spec.initial_env['DEBUG'] == 'true'

            # Check that default environment variables are still present
            assert 'OPENVSCODE_SERVER_ROOT' in spec.initial_env
            assert 'OH_ENABLE_VNC' in spec.initial_env
            assert 'LOG_JSON' in spec.initial_env