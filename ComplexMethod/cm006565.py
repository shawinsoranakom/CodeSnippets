def test_multiple_files_combined_transcription(self, mock_vlmrun_class, component_class, default_kwargs):
        """Test processing multiple files returns combined transcription."""
        # Create mock objects using helper methods
        mock_usage_1 = self._create_mock_usage(total_tokens=50)
        mock_usage_2 = self._create_mock_usage(total_tokens=60)

        segments_1 = [{"audio": {"content": "File 1 content"}}]
        segments_2 = [{"audio": {"content": "File 2 content"}}]

        mock_response_1 = self._create_mock_response("pred-1", segments_1, 5, mock_usage_1)
        mock_response_2 = self._create_mock_response("pred-2", segments_2, 7, mock_usage_2)

        # Configure mock client to return different responses for each call
        mock_client = Mock()
        mock_client.audio.generate.side_effect = [mock_response_1, mock_response_2]
        mock_client.predictions.wait.side_effect = [mock_response_1, mock_response_2]
        mock_vlmrun_class.return_value = mock_client

        component = component_class(**default_kwargs)
        component.media_files = ["/path/to/file1.mp3", "/path/to/file2.mp3"]

        result = component.process_media()

        if not isinstance(result, Data):
            pytest.fail(f"Expected result to be Data instance, got {type(result)}")
        if "results" not in result.data:
            pytest.fail("results not found in result.data")
        expected_file_count = 2
        if len(result.data["results"]) != expected_file_count:
            pytest.fail(f"Expected {expected_file_count} results, got {len(result.data['results'])}")
        if result.data["total_files"] != expected_file_count:
            pytest.fail(f"Expected total_files to be {expected_file_count}, got {result.data['total_files']}")

        # Verify individual transcription results are accessible
        if result.data["results"][0]["transcription"] != "File 1 content":
            pytest.fail(
                f"Expected first transcription to be 'File 1 content', "
                f"got '{result.data['results'][0]['transcription']}'"
            )
        if result.data["results"][1]["transcription"] != "File 2 content":
            pytest.fail(
                f"Expected second transcription to be 'File 2 content', "
                f"got '{result.data['results'][1]['transcription']}'"
            )
        if result.data["results"][0]["filename"] != "file1.mp3":
            pytest.fail(f"Expected first filename to be 'file1.mp3', got '{result.data['results'][0]['filename']}'")
        if result.data["results"][1]["filename"] != "file2.mp3":
            pytest.fail(f"Expected second filename to be 'file2.mp3', got '{result.data['results'][1]['filename']}'")

        # Verify the client was called correctly for both files
        if mock_client.audio.generate.call_count != expected_file_count:
            pytest.fail(
                f"Expected audio.generate to be called {expected_file_count} times, "
                f"got {mock_client.audio.generate.call_count}"
            )
        if mock_client.predictions.wait.call_count != expected_file_count:
            pytest.fail(
                f"Expected predictions.wait to be called {expected_file_count} times, "
                f"got {mock_client.predictions.wait.call_count}"
            )

        # Verify API key was passed correctly
        mock_vlmrun_class.assert_called_once_with(api_key="test-api-key")  # pragma: allowlist secret

        # Verify predictions.wait was called with correct IDs and timeout
        wait_calls = mock_client.predictions.wait.call_args_list
        default_timeout = 600
        if wait_calls[0][0][0] != "pred-1":
            pytest.fail(f"Expected first wait call ID to be 'pred-1', got '{wait_calls[0][0][0]}'")
        if wait_calls[0][1]["timeout"] != default_timeout:
            pytest.fail(f"Expected first wait call timeout to be {default_timeout}, got {wait_calls[0][1]['timeout']}")
        if wait_calls[1][0][0] != "pred-2":
            pytest.fail(f"Expected second wait call ID to be 'pred-2', got '{wait_calls[1][0][0]}'")
        if wait_calls[1][1]["timeout"] != default_timeout:
            pytest.fail(f"Expected second wait call timeout to be {default_timeout}, got {wait_calls[1][1]['timeout']}")