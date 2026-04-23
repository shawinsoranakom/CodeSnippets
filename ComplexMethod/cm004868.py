def convert_tr_ocr_checkpoint(checkpoint_url, pytorch_dump_folder_path):
    """
    Copy/paste/tweak model's weights to our VisionEncoderDecoderModel structure.
    """
    # define encoder and decoder configs based on checkpoint_url
    encoder_config = ViTConfig(image_size=384, qkv_bias=False)
    decoder_config = TrOCRConfig()

    # size of the architecture
    if "base" in checkpoint_url:
        decoder_config.encoder_hidden_size = 768
    elif "large" in checkpoint_url:
        # use ViT-large encoder
        encoder_config.hidden_size = 1024
        encoder_config.intermediate_size = 4096
        encoder_config.num_hidden_layers = 24
        encoder_config.num_attention_heads = 16
        decoder_config.encoder_hidden_size = 1024
    else:
        raise ValueError("Should either find 'base' or 'large' in checkpoint URL")

    # the large-printed + stage1 checkpoints uses sinusoidal position embeddings, no layernorm afterwards
    if "large-printed" in checkpoint_url or "stage1" in checkpoint_url:
        decoder_config.tie_word_embeddings = False
        decoder_config.activation_function = "relu"
        decoder_config.max_position_embeddings = 1024
        decoder_config.scale_embedding = True
        decoder_config.use_learned_position_embeddings = False
        decoder_config.layernorm_embedding = False

    # load HuggingFace model
    encoder = ViTModel(encoder_config, add_pooling_layer=False)
    decoder = TrOCRForCausalLM(decoder_config)
    model = VisionEncoderDecoderModel(encoder=encoder, decoder=decoder)
    model.eval()

    # load state_dict of original model, rename some keys
    state_dict = torch.hub.load_state_dict_from_url(checkpoint_url, map_location="cpu", check_hash=True)["model"]

    rename_keys = create_rename_keys(encoder_config, decoder_config)
    for src, dest in rename_keys:
        rename_key(state_dict, src, dest)
    read_in_q_k_v(state_dict, encoder_config)

    # remove parameters we don't need
    del state_dict["encoder.deit.head.weight"]
    del state_dict["encoder.deit.head.bias"]
    del state_dict["decoder.version"]

    # add prefix to decoder keys
    for key, val in state_dict.copy().items():
        val = state_dict.pop(key)
        if key.startswith("decoder") and "output_projection" not in key:
            state_dict["decoder.model." + key] = val
        else:
            state_dict[key] = val

    # load state dict
    model.load_state_dict(state_dict)

    # Check outputs on an image
    image_processor = ViTImageProcessor(size=encoder_config.image_size)
    tokenizer = RobertaTokenizer.from_pretrained("FacebookAI/roberta-large")
    processor = TrOCRProcessor(image_processor, tokenizer)

    pixel_values = processor(images=prepare_img(checkpoint_url), return_tensors="pt").pixel_values

    # verify logits
    decoder_input_ids = torch.tensor([[model.config.decoder.decoder_start_token_id]])
    outputs = model(pixel_values=pixel_values, decoder_input_ids=decoder_input_ids)
    logits = outputs.logits

    expected_shape = torch.Size([1, 1, 50265])
    if "trocr-base-handwritten" in checkpoint_url:
        expected_slice = torch.tensor(
            [-1.4502, -4.6683, -0.5347, -2.9291, 9.1435, -3.0571, 8.9764, 1.7560, 8.7358, -1.5311]
        )
    elif "trocr-large-handwritten" in checkpoint_url:
        expected_slice = torch.tensor(
            [-2.6437, -1.3129, -2.2596, -5.3455, 6.3539, 1.7604, 5.4991, 1.4702, 5.6113, 2.0170]
        )
    elif "trocr-base-printed" in checkpoint_url:
        expected_slice = torch.tensor(
            [-5.6816, -5.8388, 1.1398, -6.9034, 6.8505, -2.4393, 1.2284, -1.0232, -1.9661, -3.9210]
        )
    elif "trocr-large-printed" in checkpoint_url:
        expected_slice = torch.tensor(
            [-6.0162, -7.0959, 4.4155, -5.1063, 7.0468, -3.1631, 2.6466, -0.3081, -0.8106, -1.7535]
        )

    if "stage1" not in checkpoint_url:
        assert logits.shape == expected_shape, "Shape of logits not as expected"
        assert torch.allclose(logits[0, 0, :10], expected_slice, atol=1e-3), "First elements of logits not as expected"

    Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
    print(f"Saving model to {pytorch_dump_folder_path}")
    model.save_pretrained(pytorch_dump_folder_path)
    print(f"Saving processor to {pytorch_dump_folder_path}")
    processor.save_pretrained(pytorch_dump_folder_path)