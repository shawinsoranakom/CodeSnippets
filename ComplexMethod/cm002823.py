def convert_fastvlm_to_hf(text_model_id, vision_model_id, output_hub_path, old_state_dict_id):
    torch.set_default_dtype(torch.bfloat16)

    text_config = AutoConfig.from_pretrained(text_model_id)
    vision_config = AutoConfig.from_pretrained(vision_model_id)
    vision_config.model_args = {"inference_mode": True}
    vision_config.hidden_size = vision_config.num_features
    vision_config.label2id = {}
    vision_config.id2label = {}
    config = FastVlmConfig(
        text_config=text_config,
        vision_config=vision_config,
    )
    config.vision_feature_select_strategy = "full"
    config.vision_feature_layer = -1
    config.image_token_index = 151646
    config.image_seq_length = 256

    tokenizer = AutoTokenizer.from_pretrained(
        text_model_id,
        chat_template="{% for message in messages %}{% if loop.first and messages[0]['role'] != 'system' %}{{ '<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n' }}{% endif %}{{'<|im_start|>' + message['role'] + '\n'}}{# Render all images first #}{% for content in message['content'] | selectattr('type', 'equalto', 'image') %}{{ '<image>' }}{% endfor %}{# Render all text next #}{% for content in message['content'] | selectattr('type', 'equalto', 'text') %}{{ '\n' + content['text'] }}{% endfor %}{{'<|im_end|>' + '\n'}}{% endfor %}{% if add_generation_prompt %}{{ '<|im_start|>assistant\n' }}{% endif %}",
    )

    tokenizer.add_tokens(AddedToken("<image>", special=True, normalized=False), special_tokens=True)
    image_processor = CLIPImageProcessor(
        crop_size={"height": 1024, "width": 1024},
        image_mean=[0.0, 0.0, 0.0],
        image_std=[1.0, 1.0, 1.0],
        size={"shortest_edge": 1024},
    )

    processor = LlavaProcessor(tokenizer=tokenizer, image_processor=image_processor)
    processor.patch_size = 64  # effective patch size (2^6)

    model = FastVlmForConditionalGeneration(config)

    state_dict = load_original_state_dict(old_state_dict_id)
    state_dict = convert_state_dict_to_hf(state_dict)
    model.load_state_dict(state_dict, strict=True, assign=True)

    pre_expansion_embeddings = model.language_model.embed_tokens.weight.data
    mu = torch.mean(pre_expansion_embeddings, dim=0).float()
    n = pre_expansion_embeddings.size()[0]
    sigma = ((pre_expansion_embeddings - mu).T @ (pre_expansion_embeddings - mu)) / n
    dist = torch.distributions.multivariate_normal.MultivariateNormal(mu, covariance_matrix=1e-5 * sigma)

    # We add an image token so we resize the model and pad to 64 for performance reasons
    pad_shape = 64
    vocab_size = config.text_config.vocab_size
    model.resize_token_embeddings(config.text_config.vocab_size + 1, pad_shape)
    model.language_model.embed_tokens.weight.data[vocab_size:] = torch.stack(
        tuple(dist.sample() for _ in range(model.language_model.embed_tokens.weight.data[vocab_size:].shape[0])),
        dim=0,
    )
    model.lm_head.weight.data[vocab_size:] = torch.stack(
        tuple(dist.sample() for _ in range(model.lm_head.weight.data[vocab_size:].shape[0])),
        dim=0,
    )

    conversation = [{"role": "user", "content": [{"type": "text", "text": "What are these?"}, {"type": "image"}]}]
    prompt = tokenizer.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)

    url = "http://images.cocodataset.org/val2017/000000039769.jpg"
    with httpx.stream("GET", url) as response:
        raw_image = Image.open(BytesIO(response.read()))
    inputs = processor(images=raw_image, text=prompt, return_tensors="pt").to("cuda")
    inputs = {k: (v.to(torch.bfloat16) if v.dtype == torch.float32 else v) for k, v in inputs.items()}

    model = model.cuda()
    model.eval()
    with torch.no_grad():
        logits = model(**inputs).logits

    # in order to get the same logits as in the Apple repo, we need to manually replace the original (Apple) LayerNorm2D with Timm's LayerNorm2D or vice versa
    # otherwise numerical errors accumulate
    if output_hub_path == "KamilaMila/FastVLM-0.5B":
        expected_shape = torch.Size([1, 280, 152000])
        expected_slice = torch.tensor([4.1250, 9.6875, 11.1875], device="cuda")
    elif output_hub_path == "KamilaMila/FastVLM-1.5B":
        expected_shape = torch.Size([1, 280, 152000])
        expected_slice = torch.tensor([3.3750, 11.5000, 11.8125], device="cuda")
    elif output_hub_path == "KamilaMila/FastVLM-7B":
        expected_shape = torch.Size([1, 280, 152128])
        expected_slice = torch.tensor([3.8281, 9.0625, 7.9062], device="cuda")

    logits_slice = logits[0, -1, :3]
    assert torch.allclose(expected_slice, logits_slice, atol=1e-8)
    assert logits.shape == expected_shape

    model.push_to_hub(output_hub_path)
    processor.push_to_hub(output_hub_path)
    print("Successfully pushed to hub!")