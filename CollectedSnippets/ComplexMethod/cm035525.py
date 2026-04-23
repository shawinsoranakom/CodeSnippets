def test_environment_isolation(self):
        """Test that environment changes don't affect subsequent calls."""
        # First call with some environment variables
        env_vars_1 = {
            'OH_AGENT_SERVER_ENV': '{"VAR1": "value1", "VAR2": "value2"}',
        }

        with patch.dict(os.environ, env_vars_1, clear=True):
            specs_1 = get_default_docker_sandbox_specs()
            spec_1 = specs_1[0]

            assert 'VAR1' in spec_1.initial_env
            assert 'VAR2' in spec_1.initial_env
            assert spec_1.initial_env['VAR1'] == 'value1'
            assert spec_1.initial_env['VAR2'] == 'value2'

        # Second call with different environment variables
        env_vars_2 = {
            'OH_AGENT_SERVER_ENV': '{"VAR3": "value3", "VAR4": "value4"}',
        }

        with patch.dict(os.environ, env_vars_2, clear=True):
            specs_2 = get_default_docker_sandbox_specs()
            spec_2 = specs_2[0]

            # Should only have the new variables
            assert 'VAR3' in spec_2.initial_env
            assert 'VAR4' in spec_2.initial_env
            assert spec_2.initial_env['VAR3'] == 'value3'
            assert spec_2.initial_env['VAR4'] == 'value4'

            # Should not have the old variables
            assert 'VAR1' not in spec_2.initial_env
            assert 'VAR2' not in spec_2.initial_env