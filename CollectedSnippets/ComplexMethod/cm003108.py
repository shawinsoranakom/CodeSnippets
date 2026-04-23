def convert_florence2_checkpoint(hf_model_id, pytorch_dump_folder, output_hub_path):
    """
    Function to convert the microsoft florence2 checkpoint to huggingface checkpoint
    """

    hf_config = AutoConfig.from_pretrained(hf_model_id, trust_remote_code=True)
    hf_model = AutoModelForCausalLM.from_pretrained(
        hf_model_id, trust_remote_code=True, dtype=torch.float16, attn_implementation="eager"
    )
    hf_processor = AutoProcessor.from_pretrained(hf_model_id, trust_remote_code=True)
    huggingface_weights = OrderedDict()
    list_of_state_dict = []

    image_processor = hf_processor.image_processor

    tokenizer = hf_processor.tokenizer
    tokenizer.image_token = "<image>"
    tokenizer.add_tokens(AddedToken(tokenizer.image_token, special=True, normalized=False), special_tokens=True)
    tokenizer.image_token_id = tokenizer.encode(tokenizer.image_token, add_special_tokens=False)[0]

    post_processor_config = {
        "ocr": {
            "pattern": r"(.+?)<loc_(\d+)><loc_(\d+)><loc_(\d+)><loc_(\d+)><loc_(\d+)><loc_(\d+)><loc_(\d+)><loc_(\d+)>",
            "area_threshold": 0.0,
        },
        "phrase_grounding": {
            "banned_grounding_tokens": [
                "it",
                "I",
                "me",
                "mine",
                "you",
                "your",
                "yours",
                "he",
                "him",
                "his",
                "she",
                "her",
                "hers",
                "they",
                "them",
                "their",
                "theirs",
                "one",
                "oneself",
                "we",
                "us",
                "our",
                "ours",
                "you",
                "your",
                "yours",
                "they",
                "them",
                "their",
                "theirs",
                "mine",
                "yours",
                "his",
                "hers",
                "its",
                "ours",
                "yours",
                "theirs",
                "myself",
                "yourself",
                "himself",
                "herself",
                "itself",
                "ourselves",
                "yourselves",
                "themselves",
                "this",
                "that",
                "these",
                "those",
                "who",
                "whom",
                "whose",
                "which",
                "what",
                "who",
                "whom",
                "whose",
                "which",
                "that",
                "all",
                "another",
                "any",
                "anybody",
                "anyone",
                "anything",
                "each",
                "everybody",
                "everyone",
                "everything",
                "few",
                "many",
                "nobody",
                "none",
                "one",
                "several",
                "some",
                "somebody",
                "someone",
                "something",
                "each other",
                "one another",
                "myself",
                "yourself",
                "himself",
                "herself",
                "itself",
                "ourselves",
                "yourselves",
                "themselves",
                "the image",
                "image",
                "images",
                "the",
                "a",
                "an",
                "a group",
                "other objects",
                "lots",
                "a set",
            ],
        },
        "pure_text": {},
        "description_with_bboxes": {},
        "description_with_polygons": {},
        "polygons": {},
        "bboxes": {},
        "description_with_bboxes_or_polygons": {},
    }
    processor = Florence2Processor(
        image_processor=image_processor, tokenizer=tokenizer, post_processor_config=post_processor_config
    )

    vision_config = convert_config(hf_config.vision_config.__dict__)
    text_config = hf_config.text_config.__dict__
    if text_config.get("model_type") == "florence2_language":
        text_config["model_type"] = "bart"

    config = Florence2Config(
        text_config=text_config,
        vision_config=vision_config,
        image_token_id=tokenizer.image_token_id,
        dtype=torch.float16,
    )

    for stage_idx in range(len(config.vision_config.embed_dim)):
        list_of_state_dict = list_of_state_dict + vision_conv_embeddings(stage_idx)
        for block_idx in range(config.vision_config.depths[stage_idx]):
            list_of_state_dict = list_of_state_dict + vision_spatial_block(stage_idx, block_idx)
            list_of_state_dict = list_of_state_dict + vision_channel_block(stage_idx, block_idx)

    original_weights = hf_model.state_dict()
    list_of_state_dict = list_of_state_dict + multi_modal_projector()
    list_of_state_dict = list_of_state_dict + language_model(original_weights)
    for i in range(len(list_of_state_dict)):
        if list_of_state_dict[i][0] == "image_projection":
            original_weights[list_of_state_dict[i][0]].transpose_(1, 0)
        huggingface_weights[list_of_state_dict[i][1]] = original_weights[list_of_state_dict[i][0]]

    model = Florence2ForConditionalGeneration(config)
    model.load_state_dict(huggingface_weights, strict=True, assign=True)
    model.tie_weights()
    # We add an image token so we resize the model and pad to 64 for performance reasons
    pad_shape = 64
    model.resize_token_embeddings(len(tokenizer), pad_shape)

    if pytorch_dump_folder:
        model.save_pretrained(pytorch_dump_folder)
        processor.save_pretrained(pytorch_dump_folder)

    if output_hub_path:
        model.push_to_hub(output_hub_path)
        processor.push_to_hub(output_hub_path)