def test_remote_specs_include_agent_server_env(self):
        """Test that Remote sandbox specs include agent server environment variables."""
        env_vars = {
            'OH_AGENT_SERVER_ENV': '{"REMOTE_VAR": "remote_value", "API_KEY": "secret123"}',
        }

        with patch.dict(os.environ, env_vars, clear=True):
            specs = get_default_remote_sandbox_specs()

            assert len(specs) == 1
            spec = specs[0]

            # Check that custom environment variables are included
            assert 'REMOTE_VAR' in spec.initial_env
            assert spec.initial_env['REMOTE_VAR'] == 'remote_value'
            assert 'API_KEY' in spec.initial_env
            assert spec.initial_env['API_KEY'] == 'secret123'

            # Check that default environment variables are still present
            assert 'OH_CONVERSATIONS_PATH' in spec.initial_env
            assert 'OH_BASH_EVENTS_DIR' in spec.initial_env
            assert 'OH_VSCODE_PORT' in spec.initial_env