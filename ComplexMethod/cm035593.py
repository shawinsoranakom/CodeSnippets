async def test_container_to_sandbox_info_running(
        self, service, mock_running_container
    ):
        """Test conversion of running container to SandboxInfo."""
        # Execute
        result = await service._container_to_sandbox_info(mock_running_container)

        # Verify
        assert result is not None
        assert result.id == 'oh-test-abc123'
        assert result.created_by_user_id is None
        assert result.sandbox_spec_id == 'spec456'
        assert result.status == SandboxStatus.RUNNING
        assert result.session_api_key == 'session_key_123'
        assert len(result.exposed_urls) == 2

        # Check exposed URLs
        agent_url = next(url for url in result.exposed_urls if url.name == AGENT_SERVER)
        assert agent_url.url == 'http://localhost:12345'

        vscode_url = next(url for url in result.exposed_urls if url.name == VSCODE)
        assert (
            vscode_url.url
            == 'http://localhost:12346/?tkn=session_key_123&folder=/workspace'
        )