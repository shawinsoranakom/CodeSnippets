def test_qwen3_omni_get_updates_use_audio_in_video(
    mock_qwen3_omni_config,
    mock_processor,
    mock_tokenizer,
    mock_image_processor,
):
    """Test the get_updates_use_audio_in_video method directly."""

    from vllm.model_executor.models.qwen3_omni_moe_thinker import (
        Qwen3OmniMoeThinkerMultiModalProcessor,
        Qwen3OmniMoeThinkerProcessingInfo,
    )

    # Create a mock context
    mock_ctx = Mock(spec=InputProcessingContext)

    # Create processing info
    info = Qwen3OmniMoeThinkerProcessingInfo(mock_ctx)
    info._get_expected_hidden_size = lambda: 100
    info.get_hf_config = Mock(return_value=mock_qwen3_omni_config)
    info.get_hf_processor = Mock(return_value=mock_processor)
    info.get_tokenizer = Mock(return_value=mock_tokenizer)
    info.get_image_processor = Mock(return_value=mock_image_processor)

    # Create a mock dummy_inputs builder
    mock_dummy_inputs = Mock()

    # Create the processor
    processor = Qwen3OmniMoeThinkerMultiModalProcessor(info, mock_dummy_inputs)

    # Test parameters from reference video
    # https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-Omni/demo/draw.mp4
    audio_len = 85
    video_grid_thw = [6, 36, 64]
    video_second_per_grid_t = 2.0

    # Call the method
    updates = processor.get_updates_use_audio_in_video(
        thinker_config=mock_qwen3_omni_config,
        audio_len=audio_len,
        video_grid_thw=video_grid_thw,
        video_second_per_grid_t=video_second_per_grid_t,
    )

    # Updated input ids should align with HF implementation.
    # 151669,
    # <|video_pad|> * 576, <|audio_pad|> * 25,
    # <|video_pad|> * 576, <|audio_pad|> * 25,
    # <|video_pad|> * 576, <|audio_pad|> * 25,
    # <|video_pad|> * 576, <|audio_pad|> * 10,
    # <|video_pad|> * 1152,
    # 151670
    print_input_ids(updates)

    # Verify structure
    assert isinstance(updates, list)
    assert len(updates) > 0

    # Verify start and end tokens
    audio_start_token_id = mock_qwen3_omni_config.audio_start_token_id
    audio_end_token_id = mock_qwen3_omni_config.audio_end_token_id

    assert updates[0] == audio_start_token_id
    assert updates[-1] == audio_end_token_id

    # Verify both audio and video tokens are present
    audio_token_id = mock_qwen3_omni_config.audio_token_id
    video_token_id = mock_qwen3_omni_config.video_token_id

    audio_count = updates.count(audio_token_id)
    video_count = updates.count(video_token_id)

    assert audio_count == audio_len, (
        f"Expected {audio_len} audio tokens, got {audio_count}"
    )

    # Calculate expected video token count
    spatial_merge_size = mock_qwen3_omni_config.vision_config.spatial_merge_size
    height = video_grid_thw[1] // spatial_merge_size
    width = video_grid_thw[2] // spatial_merge_size
    expected_video_count = video_grid_thw[0] * height * width

    assert video_count == expected_video_count, (
        f"Expected {expected_video_count} video tokens, got {video_count}"
    )

    # Total tokens should be: 1 (start) + audio_len + video_count + 1 (end)
    expected_total = 1 + audio_len + expected_video_count + 1
    assert len(updates) == expected_total, (
        f"Expected {expected_total} total tokens, got {len(updates)}"
    )