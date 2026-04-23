def build_embedding_inputs_from_test_info(
    test_info: VLMTestInfo,
    image_assets: ImageTestAssets,
    size_wrapper: ImageSizeWrapper,
):
    # These conditions will always be true if invoked through filtering,
    # but we still check them in case this is ever called directly
    if test_info.prompt_formatter is None:
        raise ValueError("Prompt formatter must be set to build image embedding inputs")
    if size_wrapper.type != SizeType.SIZE_FACTOR or not all(
        factor == 1.0 for factor in size_wrapper.data
    ):
        raise ValueError("Embedding tests require constant (1.0) size factors")
    if test_info.convert_assets_to_embeddings is None:
        raise ValueError("No conversion func for getting embeddings found")

    model_prompts = get_model_prompts(
        SINGLE_IMAGE_BASE_PROMPTS,
        test_info.img_idx_to_prompt,
        test_info.video_idx_to_prompt,
        test_info.audio_idx_to_prompt,
        test_info.prompt_formatter,
    )

    images = [asset.pil_image for asset in image_assets]
    embeds = test_info.convert_assets_to_embeddings(image_assets)
    if test_info.dtype != "auto":
        dtype = getattr(torch, test_info.dtype)  # type: ignore
        embeds = [e.to(dtype=dtype) for e in embeds]
    assert len(images) == len(model_prompts)

    inputs = build_single_image_inputs(images, model_prompts, size_wrapper)
    vllm_embeddings = build_single_image_inputs(embeds, model_prompts, size_wrapper)
    return inputs, vllm_embeddings