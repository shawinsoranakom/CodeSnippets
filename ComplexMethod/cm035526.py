def test_llm_env_vars_propagated_to_container_run(self):
        """Test that LLM_* env vars are included in docker container.run() environment argument."""
        from unittest.mock import patch

        # Set up environment with LLM_* variables
        env_vars = {
            'LLM_TIMEOUT': '3600',
            'LLM_NUM_RETRIES': '10',
            'LLM_MODEL': 'gpt-4',
            'OTHER_VAR': 'should_not_be_forwarded',
        }

        with patch.dict(os.environ, env_vars, clear=True):
            # Create a sandbox spec using the actual factory to get LLM_* vars
            specs = get_default_docker_sandbox_specs()
            sandbox_spec = specs[0]

            # Verify the sandbox spec has the LLM_* variables
            assert 'LLM_TIMEOUT' in sandbox_spec.initial_env
            assert sandbox_spec.initial_env['LLM_TIMEOUT'] == '3600'
            assert 'LLM_NUM_RETRIES' in sandbox_spec.initial_env
            assert sandbox_spec.initial_env['LLM_NUM_RETRIES'] == '10'
            assert 'LLM_MODEL' in sandbox_spec.initial_env
            assert sandbox_spec.initial_env['LLM_MODEL'] == 'gpt-4'
            # Non-LLM_* variables should not be included
            assert 'OTHER_VAR' not in sandbox_spec.initial_env