def convert_dia_model_to_hf(checkpoint_path, verbose=False):
    """
    Converts a Dia model in Nari Labs format to Hugging Face format.
    Args:
        checkpoint_path (`str`):
            Path to the downloaded checkpoints.
        verbose (`bool`, *optional*)
            Whether to print information during conversion.
    """
    # Download from HF Hub if checkpoint_path is None
    checkpoint_path = snapshot_download(repo_id=checkpoint_path, allow_patterns=["*.pth", "*.safetensors"])
    print(f"Downloaded checkpoint from Hugging Face Hub: {checkpoint_path}")

    # Initialize base model with default config == 1.6B model
    with torch.device("meta"):
        hf_model = DiaForConditionalGeneration(config=DiaConfig())
    hf_model_dict = hf_model.state_dict()
    hf_model_keys = hf_model_dict.keys()

    # Iterate through dir to catch all respective files - prefers safetensors but allows pt
    files = os.listdir(checkpoint_path)
    for file in files:
        if file.endswith(".safetensors"):
            load_function = load_file
        elif file.endswith(".pth"):
            load_function = torch.load
    checkpoint_path = os.path.join(checkpoint_path, files[0])
    nari_state_dict = load_function(checkpoint_path, "cpu")

    # Conversion starts here
    converted_state_dict = {}
    embeddings = {}
    for key, tensor in nari_state_dict.items():
        # add prefix
        key = "model." + key

        # rename some weights
        for original, rename in rename_mapping.items():
            if original in key:
                key = re.sub(original, rename, key)

        # decoder multi channel
        if "embeddings" in key:
            embeddings_key = key.rsplit(".", 2)[0] + ".embed.weight"
            if embeddings_key in embeddings:
                embeddings[embeddings_key] += [tensor]
            else:
                embeddings[embeddings_key] = [tensor]
            continue
        elif re.sub(r"\d+", "*", key).removeprefix("model.") in shape_mappings:
            # add exception to the head
            if "logits_dense" in key:
                key = re.sub("decoder.logits_dense", "logits_dense", key).removeprefix("model.")

            # dense general
            if key in hf_model_keys:
                tensor_shape = tensor.shape
                target_shape = hf_model_dict[key].shape
                try:
                    tensor = tensor.reshape(target_shape[1], target_shape[0]).T
                    if verbose:
                        print(f"{key}: transpose reshaped from {tensor_shape} to {target_shape}")
                except Exception as e:
                    print(f"WARNING: Could not reshape {key}: {e}")

        converted_state_dict[key] = tensor

    # Combining the embeddings as last step
    embeddings = {k: torch.cat(v, dim=0) for k, v in embeddings.items()}
    converted_state_dict.update(embeddings)

    # Load converted weights into HF model
    hf_model.load_state_dict(converted_state_dict, assign=True)

    # Overwrite generation config
    hf_model.generation_config = get_generation_config(DiaConfig())

    return hf_model