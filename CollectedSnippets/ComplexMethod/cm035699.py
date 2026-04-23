def test_multiple_operations_in_single_batch(self, batched_store, mock_client):
        # Perform multiple operations
        batched_store.write('/file1.txt', 'Content 1')
        batched_store.write('/file2.txt', 'Content 2')
        batched_store.delete('/file3.txt')

        # Wait for the batch timeout
        time.sleep(0.2)

        # Check that only one POST request was made with all operations
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert args[0] == 'http://example.com'
        assert 'json' in kwargs

        # Check the batch payload
        batch_payload = kwargs['json']
        assert isinstance(batch_payload, list)
        assert len(batch_payload) == 3

        # Check each operation in the batch
        operations = {item['path']: item for item in batch_payload}

        assert '/file1.txt' in operations
        assert operations['/file1.txt']['method'] == 'POST'
        assert operations['/file1.txt']['content'] == 'Content 1'

        assert '/file2.txt' in operations
        assert operations['/file2.txt']['method'] == 'POST'
        assert operations['/file2.txt']['content'] == 'Content 2'

        assert '/file3.txt' in operations
        assert operations['/file3.txt']['method'] == 'DELETE'
        assert 'content' not in operations['/file3.txt']