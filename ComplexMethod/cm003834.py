def convert_model(input_path_or_repo, revision=None):
    original_directory = snapshot_download(
        repo_id=input_path_or_repo, revision=revision, allow_patterns=["*.safetensors"]
    )

    # Load and merge original state dict
    original_state_dict = {}
    for path in sorted(glob.glob(f"{original_directory}/*.safetensors")):
        with safetensors.torch.safe_open(path, framework="pt", device="cpu") as f:
            for key in f.keys():
                original_state_dict[key] = f.get_tensor(key)

    # Merge PartiallyFrozenEmbedding weights
    if "embed_tokens.embedding_frozen.weight" in original_state_dict:
        original_state_dict["embed_tokens.weight"] = torch.cat(
            [
                original_state_dict.pop("embed_tokens.embedding_frozen.weight"),
                original_state_dict.pop("embed_tokens.embedding_trainable.weight"),
            ],
            dim=0,
        )

    # Merge PartiallyFrozenLinear weights for audio_lm_head
    if "audio_decoder_proj.audio_lm_head.linear_frozen.weight" in original_state_dict:
        original_state_dict["audio_decoder_proj.audio_lm_head.weight"] = torch.cat(
            [
                original_state_dict.pop("audio_decoder_proj.audio_lm_head.linear_frozen.weight"),
                original_state_dict.pop("audio_decoder_proj.audio_lm_head.linear_trainable.weight"),
            ],
            dim=0,
        )

    # Merge PartiallyFrozenLinear weights for text_lm_head
    if "audio_decoder_proj.text_lm_head.linear_frozen.weight" in original_state_dict:
        original_state_dict["audio_decoder_proj.text_lm_head.weight"] = torch.cat(
            [
                original_state_dict.pop("audio_decoder_proj.text_lm_head.linear_frozen.weight"),
                original_state_dict.pop("audio_decoder_proj.text_lm_head.linear_trainable.weight"),
            ],
            dim=0,
        )

    # Convert keys
    state_dict = {}
    for key, tensor in original_state_dict.items():
        if any(key.endswith(ignored) for ignored in KEYS_TO_IGNORE):
            continue
        state_dict[convert_key(key, ORIGINAL_TO_CONVERTED_KEY_MAPPING)] = tensor

    # Keep audio_decoder_proj-prefixed lm_head weights alongside the stripped versions
    if "audio_lm_head.weight" in state_dict:
        state_dict["audio_decoder_proj.audio_lm_head.weight"] = state_dict["audio_lm_head.weight"]
    if "text_lm_head.weight" in state_dict:
        state_dict["audio_decoder_proj.text_lm_head.weight"] = state_dict["text_lm_head.weight"]

    # Load into model (use_text_head=True to include text_lm_head)
    config = HiggsAudioV2Config(codebook_size=1026)
    with torch.device("meta"):
        model = HiggsAudioV2ForConditionalGeneration(config, use_text_head=True)
    model._keys_to_ignore_on_load_unexpected = [
        "audio_decoder_proj.audio_lm_head.weight",
        "audio_decoder_proj.text_lm_head.weight",
    ]
    model.load_state_dict(state_dict, strict=False, assign=True)

    model.generation_config._from_model_config = False
    model.generation_config.bos_token_id = 1
    model.generation_config.eos_token_id = 128009
    model.generation_config.pad_token_id = 128001
    model.generation_config.ras_win_len = 7
    model.generation_config.ras_win_max_num_repeat = 2
    model.generation_config.use_text_head = True

    print("Model converted successfully.")

    return model