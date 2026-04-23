async def test_different_requests_get_different_clients(self, injector):
        """Test that different requests get different client instances."""
        request1 = MockRequest()
        request2 = MockRequest()

        with patch('httpx.AsyncClient') as mock_async_client:
            client1_instance = MagicMock()
            client2_instance = MagicMock()
            mock_async_client.side_effect = [client1_instance, client2_instance]

            # Get client for first request
            async for client1 in injector.depends(request1):
                assert client1 is client1_instance
                assert request1.state.httpx_client is client1_instance
                break

            # Get client for second request
            async for client2 in injector.depends(request2):
                assert client2 is client2_instance
                assert request2.state.httpx_client is client2_instance
                break

            # Verify different clients were created
            assert client1_instance is not client2_instance
            assert mock_async_client.call_count == 2