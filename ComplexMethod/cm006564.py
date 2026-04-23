def test_video_file_with_audio_content(self, mock_vlmrun_class, component_class, default_kwargs):
        """Test video file processing that includes both video and audio content."""
        # Create mock objects using helper methods
        mock_usage = self._create_mock_usage(total_tokens=300, prompt_tokens=200, completion_tokens=100)
        segments = [
            {"video": {"content": "Scene description 1"}, "audio": {"content": "Dialog line 1"}},
            {"video": {"content": "Scene description 2"}, "audio": {"content": "Dialog line 2"}},
            {"video": {"content": "Scene description 3"}},
        ]
        mock_response = self._create_mock_response("test-video-456", segments, 120.0, mock_usage)

        # Configure mock client
        mock_client = self._create_mock_vlm_client(video_response=mock_response)
        mock_vlmrun_class.return_value = mock_client

        component = component_class(**default_kwargs)
        component.media_type = "video"
        component.media_files = ["/path/to/test.mp4"]

        result = component.process_media()

        if not isinstance(result, Data):
            pytest.fail(f"Expected result to be Data instance, got {type(result)}")
        if "results" not in result.data:
            pytest.fail("results not found in result.data")
        if len(result.data["results"]) != 1:
            pytest.fail(f"Expected 1 result, got {len(result.data['results'])}")

        video_result = result.data["results"][0]
        if video_result["prediction_id"] != "test-video-456":
            pytest.fail(f"Expected prediction_id to be 'test-video-456', got '{video_result['prediction_id']}'")
        # Check that transcription includes both video content and audio in brackets
        expected_transcription = (
            "Scene description 1 [Audio: Dialog line 1] Scene description 2 [Audio: Dialog line 2] Scene description 3"
        )
        if video_result["transcription"] != expected_transcription:
            pytest.fail(f"Expected transcription mismatch, got '{video_result['transcription']}'")
        if video_result["metadata"]["media_type"] != "video":
            pytest.fail(f"Expected media_type to be 'video', got '{video_result['metadata']['media_type']}'")
        expected_video_duration = 120.0
        if video_result["metadata"]["duration"] != pytest.approx(expected_video_duration):
            pytest.fail(
                f"Expected duration to be {expected_video_duration}, got {video_result['metadata']['duration']}"
            )
        if video_result["status"] != "completed":
            pytest.fail(f"Expected status to be 'completed', got '{video_result['status']}'")
        expected_video_tokens = 300
        if video_result["usage"].total_tokens != expected_video_tokens:
            pytest.fail(
                f"Expected total_tokens to be {expected_video_tokens}, got {video_result['usage'].total_tokens}"
            )

        # Verify the client was called correctly
        mock_client.video.generate.assert_called_once()
        mock_client.predictions.wait.assert_called_once_with(mock_response.id, timeout=600)

        # Verify API key was passed correctly
        mock_vlmrun_class.assert_called_once_with(api_key="test-api-key")