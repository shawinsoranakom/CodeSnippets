def test_processor_override(
    image_assets: ImageTestAssets,
    model_id: str,
    mm_processor_kwargs: dict[str, object],
    expected_toks_per_img: int,
    expected_pixels_shape: tuple[int, int],
    num_imgs: int,
    kwargs_on_init: bool,
):
    """Ensure Qwen2VLMultiModalProcessor handles min/max pixels properly."""
    if (
        Version(TRANSFORMERS_VERSION) < Version("5.2.0")
        and "size" in mm_processor_kwargs
    ):
        pytest.skip("`size` ignored by `Qwen2VLProcessor.__call__`")

    ctx = build_model_context(
        model_id,
        mm_processor_kwargs=mm_processor_kwargs if kwargs_on_init else None,
        limit_mm_per_prompt={"image": num_imgs},
    )
    processor = MULTIMODAL_REGISTRY.create_processor(ctx.model_config)
    tokenizer = processor.info.get_tokenizer()
    hf_processor_mm_kwargs = {} if kwargs_on_init else mm_processor_kwargs

    # Build the image str / prompt based on the number of images we pass
    prompt = "<|vision_start|><|image_pad|><|vision_end|>" * num_imgs
    mm_data = {"image": [image_assets[0].pil_image] * num_imgs}

    processed_inputs = processor(
        prompt,
        mm_items=processor.info.parse_mm_data(mm_data),
        hf_processor_mm_kwargs=hf_processor_mm_kwargs,
    )

    # Ensure we have the right number of placeholders per num_crops size
    hf_processor = processor.info.get_hf_processor(**hf_processor_mm_kwargs)
    image_token_id = tokenizer.convert_tokens_to_ids(hf_processor.image_token)
    img_tok_count = processed_inputs["prompt_token_ids"].count(image_token_id)
    pixel_shape = processed_inputs["mm_kwargs"].get_data()["pixel_values"].shape

    assert img_tok_count == expected_toks_per_img * num_imgs
    assert pixel_shape[0] == expected_pixels_shape[0] * num_imgs
    assert pixel_shape[1] == expected_pixels_shape[1]