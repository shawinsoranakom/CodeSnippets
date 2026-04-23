def test_flush_sends_immediately(self, batched_store, mock_client):
        # Write a file
        batched_store.write('/test.txt', 'Hello, world!')

        # The client should not have been called yet
        mock_client.post.assert_not_called()

        # Flush the batch
        batched_store.flush()

        # Now the client should have been called without waiting for timeout
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert args[0] == 'http://example.com'
        assert 'json' in kwargs

        # Check the batch payload
        batch_payload = kwargs['json']
        assert isinstance(batch_payload, list)
        assert len(batch_payload) == 1
        assert batch_payload[0]['method'] == 'POST'
        assert batch_payload[0]['path'] == '/test.txt'
        assert batch_payload[0]['content'] == 'Hello, world!'