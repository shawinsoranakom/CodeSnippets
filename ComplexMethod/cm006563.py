def test_single_audio_file_with_mocked_client(self, mock_vlmrun_class, component_class, default_kwargs):
        """Test single audio file processing with mocked VLMRun client."""
        # Create mock objects using helper methods
        mock_usage = self._create_mock_usage(total_tokens=150, prompt_tokens=100, completion_tokens=50)
        segments = [{"audio": {"content": "Hello world"}}, {"audio": {"content": "This is a test"}}]
        mock_response = self._create_mock_response("test-prediction-123", segments, 10.5, mock_usage)

        # Configure mock client
        mock_client = self._create_mock_vlm_client(audio_response=mock_response)
        mock_vlmrun_class.return_value = mock_client

        component = component_class(**default_kwargs)
        component.media_files = ["/path/to/test.mp3"]

        result = component.process_media()

        if not isinstance(result, Data):
            pytest.fail(f"Expected result to be Data instance, got {type(result)}")
        if "results" not in result.data:
            pytest.fail("results not found in result.data")
        if len(result.data["results"]) != 1:
            pytest.fail(f"Expected 1 result, got {len(result.data['results'])}")

        audio_result = result.data["results"][0]
        if audio_result["prediction_id"] != "test-prediction-123":
            pytest.fail(f"Expected prediction_id to be 'test-prediction-123', got '{audio_result['prediction_id']}'")
        if audio_result["transcription"] != "Hello world This is a test":
            pytest.fail(f"Expected transcription mismatch, got '{audio_result['transcription']}'")
        expected_duration = 10.5
        if audio_result["metadata"]["duration"] != pytest.approx(expected_duration):
            pytest.fail(f"Expected duration to be {expected_duration}, got {audio_result['metadata']['duration']}")
        if audio_result["status"] != "completed":
            pytest.fail(f"Expected status to be 'completed', got '{audio_result['status']}'")
        expected_tokens = 150
        if audio_result["usage"].total_tokens != expected_tokens:
            pytest.fail(f"Expected total_tokens to be {expected_tokens}, got {audio_result['usage'].total_tokens}")
        if "filename" not in audio_result:
            pytest.fail("filename not found in audio_result")
        if audio_result["filename"] != "test.mp3":
            pytest.fail(f"Expected filename to be 'test.mp3', got '{audio_result['filename']}'")

        # Verify the client was called correctly
        mock_client.audio.generate.assert_called_once()
        mock_client.predictions.wait.assert_called_once_with(mock_response.id, timeout=600)

        # Verify API key was passed correctly
        mock_vlmrun_class.assert_called_once_with(
            api_key="test-api-key"  # pragma: allowlist secret
        )