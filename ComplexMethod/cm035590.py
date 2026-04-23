async def test_search_sandboxes_success(
        self, service, mock_running_container, mock_paused_container
    ):
        """Test successful search for sandboxes."""
        # Setup
        service.docker_client.containers.list.return_value = [
            mock_running_container,
            mock_paused_container,
        ]
        service.httpx_client.get.return_value.raise_for_status.return_value = None

        # Execute
        result = await service.search_sandboxes()

        # Verify
        assert isinstance(result, SandboxPage)
        assert len(result.items) == 2
        assert result.next_page_id is None

        # Verify running container
        running_sandbox = next(
            s for s in result.items if s.status == SandboxStatus.RUNNING
        )
        assert running_sandbox.id == 'oh-test-abc123'
        assert running_sandbox.created_by_user_id is None
        assert running_sandbox.sandbox_spec_id == 'spec456'
        assert running_sandbox.session_api_key == 'session_key_123'
        assert len(running_sandbox.exposed_urls) == 2

        # Verify paused container
        paused_sandbox = next(
            s for s in result.items if s.status == SandboxStatus.PAUSED
        )
        assert paused_sandbox.id == 'oh-test-def456'
        assert paused_sandbox.session_api_key is None
        assert paused_sandbox.exposed_urls is None