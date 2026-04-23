def test_multiple_updates_same_file(self, batched_store, mock_client):
        # Write to the same file multiple times
        batched_store.write('/test.txt', 'Version 1')
        batched_store.write('/test.txt', 'Version 2')
        batched_store.write('/test.txt', 'Version 3')

        # Wait for the batch timeout
        time.sleep(0.2)

        # Only the latest version should be sent
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
        assert batch_payload[0]['content'] == 'Version 3'