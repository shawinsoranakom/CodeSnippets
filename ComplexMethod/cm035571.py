def test_get_default_sandbox_specs(self):
        """Test get_default_sandbox_specs function."""
        specs = get_default_sandbox_specs()

        assert len(specs) == 1
        assert isinstance(specs[0], SandboxSpecInfo)
        assert specs[0].id.startswith('ghcr.io/openhands/agent-server:')
        assert specs[0].id.endswith('-python')
        assert specs[0].command == ['--port', '8000']
        assert 'OPENVSCODE_SERVER_ROOT' in specs[0].initial_env
        assert 'OH_ENABLE_VNC' in specs[0].initial_env
        assert 'LOG_JSON' in specs[0].initial_env
        assert specs[0].working_dir == '/workspace/project'