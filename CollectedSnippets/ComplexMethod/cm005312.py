def convert_llava_llama_to_hf(text_model_id, vision_model_id, output_hub_path, old_state_dict_id):
    torch.set_default_dtype(torch.float16)
    text_config = AutoConfig.from_pretrained(text_model_id)

    tokenizer = AutoTokenizer.from_pretrained(text_model_id)
    tokenizer.add_tokens(AddedToken("<image>", special=True, normalized=False), special_tokens=True)
    if "Qwen" not in text_model_id:  # qwen already has a pad token
        tokenizer.add_special_tokens({"pad_token": "<pad>"})

    image_processor = AutoImageProcessor.from_pretrained(vision_model_id)
    processor = LlavaProcessor(tokenizer=tokenizer, image_processor=image_processor)

    if "siglip" in vision_model_id:
        vision_config = SiglipVisionConfig(
            hidden_size=1152,
            image_size=384,
            intermediate_size=4304,
            num_attention_heads=16,
            num_hidden_layers=26,
            patch_size=14,
            vision_use_head=False,
        ).to_dict()
    else:
        vision_config = None

    config = LlavaConfig(
        text_config=text_config,
        vision_config=vision_config,
    )

    # llms-lab interleave models do not use any selection strategy except for last hidden state
    if "Qwen" in text_model_id:
        config.image_token_id = 151646
        if "siglip" in vision_model_id:
            config.vision_feature_select_strategy = "full"
            config.vision_feature_layer = -1
    else:
        config.pad_token_id = 32001
        config.image_token_id = 32000

    with torch.device("meta"):
        model = LlavaForConditionalGeneration(config)

    # Some llava variants like microsoft/llava-med-v1.5-mistral-7b use safetensors to store weights
    if file_exists(old_state_dict_id, "model_state_dict.bin"):
        state_dict_path = hf_hub_download(old_state_dict_id, "model_state_dict.bin")
        state_dict = torch.load(state_dict_path, map_location="cpu", weights_only=True)
    else:
        state_dict = load_original_state_dict(old_state_dict_id)

    state_dict = convert_state_dict_to_hf(state_dict)
    model.load_state_dict(state_dict, strict=True, assign=True)

    pre_expansion_embeddings = model.language_model.model.embed_tokens.weight.data
    mu = torch.mean(pre_expansion_embeddings, dim=0).float()
    n = pre_expansion_embeddings.size()[0]
    sigma = ((pre_expansion_embeddings - mu).T @ (pre_expansion_embeddings - mu)) / n
    dist = torch.distributions.multivariate_normal.MultivariateNormal(mu, covariance_matrix=1e-5 * sigma)

    # We add an image token so we resize the model and pad to 64 for performance reasons
    pad_shape = 64
    vocab_size = config.text_config.vocab_size
    model.resize_token_embeddings(config.text_config.vocab_size + 2, pad_shape)
    model.language_model.model.embed_tokens.weight.data[vocab_size:] = torch.stack(
        tuple(dist.sample() for _ in range(model.language_model.model.embed_tokens.weight.data[vocab_size:].shape[0])),
        dim=0,
    )
    model.language_model.lm_head.weight.data[vocab_size:] = torch.stack(
        tuple(dist.sample() for _ in range(model.language_model.lm_head.weight.data[vocab_size:].shape[0])),
        dim=0,
    )

    model.push_to_hub(output_hub_path)
    processor.push_to_hub(output_hub_path)