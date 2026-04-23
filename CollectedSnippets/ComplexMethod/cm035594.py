async def test_container_to_sandbox_info_host_network(
        self, service_with_host_network, mock_host_network_container
    ):
        """Test conversion of host network container to SandboxInfo."""
        result = await service_with_host_network._container_to_sandbox_info(
            mock_host_network_container
        )

        assert result is not None
        assert result.id == 'oh-test-abc123'
        assert result.status == SandboxStatus.RUNNING
        assert result.session_api_key == 'session_key_123'
        assert len(result.exposed_urls) == 2

        agent_url = next(url for url in result.exposed_urls if url.name == AGENT_SERVER)
        assert agent_url.url == 'http://localhost:8000'
        assert agent_url.port == 8000

        vscode_url = next(url for url in result.exposed_urls if url.name == VSCODE)
        assert (
            vscode_url.url
            == 'http://localhost:8001/?tkn=session_key_123&folder=/workspace'
        )
        assert vscode_url.port == 8001