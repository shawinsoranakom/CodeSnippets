def test_binary_content_handling(self, batched_store, mock_client):
        # Write binary content
        binary_content = b'\x00\x01\x02\x03\xff\xfe\xfd\xfc'
        batched_store.write('/binary.bin', binary_content)

        # Wait for the batch timeout
        time.sleep(0.2)

        # Check that the client was called
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert args[0] == 'http://example.com'
        assert 'json' in kwargs

        # Check the batch payload
        batch_payload = kwargs['json']
        assert isinstance(batch_payload, list)
        assert len(batch_payload) == 1

        # Binary content should be base64 encoded
        assert batch_payload[0]['method'] == 'POST'
        assert batch_payload[0]['path'] == '/binary.bin'
        assert 'content' in batch_payload[0]
        assert 'encoding' in batch_payload[0]
        assert batch_payload[0]['encoding'] == 'base64'

        # Verify the content can be decoded back to the original binary
        import base64

        decoded = base64.b64decode(batch_payload[0]['content'].encode('ascii'))
        assert decoded == binary_content