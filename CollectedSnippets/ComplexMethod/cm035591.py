async def test_start_sandbox_success(self, mock_urandom, mock_encodebytes, service):
        """Test successful sandbox startup."""
        # Setup
        mock_urandom.side_effect = [b'container_id', b'session_key']
        mock_encodebytes.side_effect = ['test_container_id', 'test_session_key']

        mock_container = MagicMock()
        mock_container.name = 'oh-test-test_container_id'
        mock_container.status = 'running'
        mock_container.image.tags = ['test-image:latest']
        mock_container.attrs = {
            'Created': '2024-01-15T10:30:00.000000000Z',
            'Config': {
                'Env': ['OH_SESSION_API_KEYS_0=test_session_key', 'TEST_VAR=test_value']
            },
            'NetworkSettings': {'Ports': {}},
        }

        service.docker_client.containers.run.return_value = mock_container

        with (
            patch.object(service, '_find_unused_port', side_effect=[12345, 12346]),
            patch.object(
                service, 'pause_old_sandboxes', return_value=[]
            ) as mock_cleanup,
        ):
            # Execute
            result = await service.start_sandbox()

        # Verify
        assert result is not None
        assert result.id == 'oh-test-test_container_id'

        # Verify cleanup was called with the correct limit
        mock_cleanup.assert_called_once_with(2)

        # Verify container was created with correct parameters
        service.docker_client.containers.run.assert_called_once()
        call_args = service.docker_client.containers.run.call_args

        assert call_args[1]['image'] == 'test-image:latest'
        assert call_args[1]['name'] == 'oh-test-test_container_id'
        assert 'OH_SESSION_API_KEYS_0' in call_args[1]['environment']
        assert (
            call_args[1]['environment']['OH_SESSION_API_KEYS_0'] == 'test_session_key'
        )
        assert call_args[1]['ports'] == {8000: 12345, 8001: 12346}
        assert call_args[1]['working_dir'] == '/workspace'
        assert call_args[1]['detach'] is True