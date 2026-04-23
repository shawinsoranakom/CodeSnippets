def test_vit_backend_functionality(
    model_key: str,
    mm_encoder_attn_backend: AttentionBackendEnum | None,
    image_assets,
    video_assets,
    vllm_runner,
    request,
):
    """Test ViT attention backend functionality for multimodal models.

    This test validates that each model can successfully generate outputs
    using different ViT attention backends. The test:
    1. Filters unsupported backends per model
    2. Applies appropriate GPU marks
    3. Routes to the correct test handler based on interface
    4. Validates output meets minimum requirements
    """
    config = MODEL_CONFIGS[model_key]

    # Step 1: Backend filtering
    if (
        "supported_backends" in config
        and mm_encoder_attn_backend is not None
        and mm_encoder_attn_backend not in config["supported_backends"]
    ):
        pytest.skip(
            f"{model_key} does not support {mm_encoder_attn_backend} backend now."
        )

    # Step 2: Apply GPU marks dynamically
    if "gpu_marks" in config:
        for mark in config["gpu_marks"]:
            request.applymarker(mark)

    # Step 3: Route to appropriate handler
    if config.get("media_type") == "video":
        run_video_test(config, mm_encoder_attn_backend, video_assets, vllm_runner)
    elif config["interface"] == "llm_chat":
        run_llm_chat_test(config, mm_encoder_attn_backend, image_assets)
    elif config["interface"] == "llm_generate":
        run_llm_generate_test(config, mm_encoder_attn_backend, image_assets)
    else:
        raise ValueError(f"Unknown interface: {config['interface']}")