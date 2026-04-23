async def test_request_state_persistence(self, injector):
        """Test that the client persists in request state across multiple resolve calls."""
        request = MockRequest()

        with patch('httpx.AsyncClient') as mock_async_client:
            mock_client_instance = MagicMock()
            mock_async_client.return_value = mock_client_instance

            # First resolve call
            async for client1 in injector.depends(request):
                assert hasattr(request.state, 'httpx_client')
                assert request.state.httpx_client is mock_client_instance
                break

            # Second resolve call - should reuse the same client
            async for client2 in injector.depends(request):
                assert client1 is client2
                assert request.state.httpx_client is mock_client_instance
                break

            # Client should still be in request state after iteration
            assert request.state.httpx_client is mock_client_instance
            # Only one client should have been created
            mock_async_client.assert_called_once()