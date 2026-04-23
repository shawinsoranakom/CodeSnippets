def build_video_inputs_from_test_info(
    test_info: VLMTestInfo,
    video_assets: VideoTestAssets,
    size_wrapper: ImageSizeWrapper,
    num_frames: int,
    needs_video_metadata: bool,
) -> list[PromptWithMultiModalInput]:
    if test_info.prompt_formatter is None:
        raise ValueError("Prompt formatter must be set to build video inputs")
    model_prompts = get_model_prompts(
        [VIDEO_BASE_PROMPT],
        test_info.img_idx_to_prompt,
        test_info.video_idx_to_prompt,
        test_info.audio_idx_to_prompt,
        test_info.prompt_formatter,
    )

    sampled_vids = [
        sample_frames_with_video_metadata(
            (asset.np_ndarrays, asset.metadata),
            num_frames,
        )
        for asset in video_assets
    ]

    video_scaler = (
        resize_video if size_wrapper.type == SizeType.FIXED_SIZE else rescale_video_size
    )

    return [
        PromptWithMultiModalInput(
            prompts=[prompt for _ in size_wrapper.data],
            video_data=[
                (
                    video_scaler(video, size)
                    if not needs_video_metadata
                    else (video_scaler(video, size), meta)
                )
                for size in size_wrapper.data
            ],
        )
        for (video, meta), prompt in zip(sampled_vids, model_prompts)
    ]