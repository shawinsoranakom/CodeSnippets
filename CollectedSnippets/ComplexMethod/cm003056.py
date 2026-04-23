def convert_llava_to_hf(model_id, pytorch_dump_folder_path, push_to_hub=False):
    # load original config
    filepath = hf_hub_download(repo_id=model_id, filename="config.json", repo_type="model")
    with open(filepath) as f:
        data = json.load(f)
        print(data)

    if model_id == "lmms-lab/LLaVA-NeXT-Video-7B-32K":
        text_model_id = "mistralai/Mistral-7B-Instruct-v0.2"
        video_token_id = 32000
        image_token_id = 32001
        overwrite_text_config = {}
    elif model_id in ["lmms-lab/LLaVA-NeXT-Video-7B", "lmms-lab/LLaVA-NeXT-Video-7B-DPO"]:
        text_model_id = "lmsys/vicuna-7b-v1.5"
        video_token_id = 32000
        image_token_id = 32001
        overwrite_text_config = {"factor": 2.0, "type": "linear"}
    elif model_id in ["lmms-lab/LLaVA-NeXT-Video-34B", "lmms-lab/LLaVA-NeXT-Video-34B-DPO"]:
        text_model_id = "NousResearch/Nous-Hermes-2-Yi-34B"
        video_token_id = 64000
        image_token_id = 64001
        overwrite_text_config = {}
    else:
        raise ValueError("Incorrect checkpoint referenced. Text model-id not identified!")

    vision_model_id = data["mm_vision_tower"]

    torch.set_default_dtype(torch.bfloat16)
    text_config = AutoConfig.from_pretrained(text_model_id)
    text_config = text_config.to_dict()
    text_config.update(overwrite_text_config)

    tokenizer = AutoTokenizer.from_pretrained(text_model_id, use_fast=True, padding_side="left")
    tokenizer.add_tokens(AddedToken("<video>", special=True, normalized=False), special_tokens=True)
    tokenizer.add_tokens(AddedToken("<image>", special=True, normalized=False), special_tokens=True)

    image_processor = LlavaNextImageProcessor.from_pretrained(vision_model_id)
    video_processor = LlavaNextVideoVideoProcessor.from_pretrained(vision_model_id)
    processor = LlavaNextVideoProcessor(
        tokenizer=tokenizer,
        video_processor=video_processor,
        image_processor=image_processor,
        chat_template=model2template[model_id],
    )

    config = LlavaNextVideoConfig(
        text_config=text_config,
        image_grid_pinpoints=image_processor.image_grid_pinpoints,
        use_image_newline_parameter=True,
        video_token_id=video_token_id,
        image_token_id=image_token_id,
    )

    with torch.device("meta"):
        model = LlavaNextVideoForConditionalGeneration(config)

    # load original state dict
    state_dict = load_original_state_dict(model_id)
    state_dict = convert_state_dict_to_hf(state_dict)
    model.load_state_dict(state_dict, assign=True, strict=True)

    # See https://nlp.stanford.edu/~johnhew/vocab-expansion.html for why we get mean/stdev this way to expand embeddings
    pre_expansion_embeddings = model.language_model.model.embed_tokens.weight.data
    mu = torch.mean(pre_expansion_embeddings, dim=0).float()
    n = pre_expansion_embeddings.size()[0]
    sigma = ((pre_expansion_embeddings - mu).T @ (pre_expansion_embeddings - mu)) / n
    dist = torch.distributions.multivariate_normal.MultivariateNormal(mu, covariance_matrix=1e-5 * sigma)

    # We add an image token so we resize the model
    # Pad to 64 for performance reasons
    pad_shape = 64
    vocab_size = config.text_config.vocab_size

    # this one has 2 additional tokens, namely <image>, <video> and <pad>
    num_tokens = vocab_size + 3
    model.resize_token_embeddings(num_tokens, pad_to_multiple_of=pad_shape)
    model.language_model.model.embed_tokens.weight.data[vocab_size:] = torch.stack(
        tuple(dist.sample() for _ in range(model.language_model.model.embed_tokens.weight.data[vocab_size:].shape[0])),
        dim=0,
    )
    model.language_model.lm_head.weight.data[vocab_size:] = torch.stack(
        tuple(dist.sample() for _ in range(model.language_model.lm_head.weight.data[vocab_size:].shape[0])),
        dim=0,
    )

    if pytorch_dump_folder_path is not None:
        print(f"Saving model and processor for {model_id} to {pytorch_dump_folder_path}")
        Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
        model.save_pretrained(pytorch_dump_folder_path)
        processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        repo_id = model_id.split("/")[-1]
        print(f"Pushing model to hub repo: {repo_id}")
        model.push_to_hub(f"llava-hf/{repo_id}-hf")
        processor.push_to_hub(f"llava-hf/{repo_id}-hf")