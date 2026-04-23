def run_intern_vit_test(
    image_assets: ImageTestAssets,
    model_id: str,
    *,
    dtype: str,
):
    model = snapshot_download(model_id, allow_patterns=DOWNLOAD_PATTERN)
    torch_dtype = STR_DTYPE_TO_TORCH_DTYPE[dtype]

    img_processor = CLIPImageProcessor.from_pretrained(model)
    images = [asset.pil_image for asset in image_assets]
    pixel_values = [
        img_processor(images, return_tensors="pt").pixel_values.to(torch_dtype)
        for images in images
    ]

    config = AutoConfig.from_pretrained(model, trust_remote_code=True)
    if not getattr(config, "norm_type", None):
        config.norm_type = "rms_norm"

    hf_model = AutoModel.from_pretrained(
        model, dtype=torch_dtype, trust_remote_code=True
    ).to(DEVICE_TYPE)
    hf_outputs_per_image = [
        hf_model(pixel_value.to(DEVICE_TYPE)).last_hidden_state
        for pixel_value in pixel_values
    ]

    from vllm.model_executor.models.intern_vit import InternVisionModel

    vllm_model = InternVisionModel(config)
    vllm_model.load_weights(hf_model.state_dict().items())

    del hf_model
    cleanup_dist_env_and_memory()

    vllm_model = vllm_model.to(DEVICE_TYPE, torch_dtype)
    vllm_outputs_per_image = [
        vllm_model(pixel_values=pixel_value.to(DEVICE_TYPE))
        for pixel_value in pixel_values
    ]
    del vllm_model
    cleanup_dist_env_and_memory()

    cos_similar = nn.CosineSimilarity(dim=-1)
    for vllm_output, hf_output in zip(vllm_outputs_per_image, hf_outputs_per_image):
        assert cos_similar(vllm_output, hf_output).mean() > 0.99