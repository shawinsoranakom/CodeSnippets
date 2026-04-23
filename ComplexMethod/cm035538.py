async def test_to_sandbox_info_with_running_runtime(self, remote_sandbox_service):
        """Test conversion to SandboxInfo with running runtime."""
        # Setup
        stored_sandbox = create_stored_sandbox()
        runtime_data = create_runtime_data(status='running')

        # Execute
        sandbox_info = remote_sandbox_service._to_sandbox_info(
            stored_sandbox, runtime_data
        )

        # Verify
        assert sandbox_info.id == 'test-sandbox-123'
        assert sandbox_info.created_by_user_id == 'test-user-123'
        assert sandbox_info.sandbox_spec_id == 'test-image:latest'
        assert sandbox_info.status == SandboxStatus.RUNNING
        assert sandbox_info.session_api_key == 'test-session-key'
        assert len(sandbox_info.exposed_urls) == 4

        # Check exposed URLs
        url_names = [url.name for url in sandbox_info.exposed_urls]
        assert AGENT_SERVER in url_names
        assert VSCODE in url_names
        assert WORKER_1 in url_names
        assert WORKER_2 in url_names