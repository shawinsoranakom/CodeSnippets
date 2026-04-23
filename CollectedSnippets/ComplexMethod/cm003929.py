def convert_colqwen2_weights_to_hf(
    model_id: str,
    output_dir: str,
    push_to_hub: bool,
    revision: str | None = None,
    original_vlm_name_or_path: str | None = None,
):
    # Load the original model data
    original_config = AutoConfig.from_pretrained(
        model_id,
        revision=revision,
    )
    if original_vlm_name_or_path is not None:
        original_config._name_or_path = original_vlm_name_or_path
    if hasattr(original_config, "architectures"):
        delattr(original_config, "architectures")

    original_state_dict = load_original_state_dict(model_id, revision=revision)

    # Format the state_dict keys
    original_state_dict = rename_state_dict_keys(original_state_dict)

    # Create the new config
    config = ColQwen2Config(
        vlm_config=original_config,
        embedding_dim=128,  # hardcoded in the original model
    )
    config.model_type = "colqwen2"
    config.is_composition = False

    # Load the untrained model
    vlm_name_or_path = getattr(config.vlm_config, "_name_or_path", None)
    if vlm_name_or_path and "2.5" in str(vlm_name_or_path):
        print(
            "Detected colqwen2.5 adapters in vlm_config; loading base model %s and merging PEFT weights."
            % vlm_name_or_path
        )
        base_model = AutoModel.from_pretrained(
            vlm_name_or_path,
            device_map="cpu",
            trust_remote_code=True,
        )
        peft_model = PeftModel.from_pretrained(base_model, model_id)
        model = peft_model.merge_and_unload()
    else:
        model = ColQwen2ForRetrieval(config=config).to("cpu").eval()
    print("Created model with new config and randomly initialized weights")

    # NOTE: The new model was initialized with float32 weights. We need to convert it to the desired precision.
    # There are two ways to set the model's dtype:
    # - Using `model.from_pretrained(..., dtype=dtype_precision)` doesn't convert the hyperparameters to the desired precision.
    # - Using `model.to(dtype_precision)` converts all values - including the hyperparameters - to the desired precision.
    # The following snippet allows a fine-grained control over the model's dtype, making sure that all
    # the new weights' dtypes match the original model.
    for param in model.parameters():
        param.data = param.data.to(ORIGINAL_DTYPE)
    print(f"Converted the new model weights to `{ORIGINAL_DTYPE}`")

    # Load the original weights
    model.load_state_dict(original_state_dict)
    print("Loaded original model weights")

    # # Sanity check: ensure all keys are the same
    state_dict_keys_old = set(original_state_dict.keys())
    state_dict_keys_new = set(model.state_dict().keys())
    disjoint_keys = state_dict_keys_old.symmetric_difference(state_dict_keys_new)
    if disjoint_keys:
        raise ValueError(f"Incompatible keys: {disjoint_keys}")

    # Save the model
    if push_to_hub:
        model.push_to_hub(output_dir, private=True)
        print(f"Model pushed to the hub at `{output_dir}`")
    else:
        Path(output_dir).mkdir(exist_ok=True, parents=True)
        model.save_pretrained(output_dir)
        print(f"Model saved to `{output_dir}`")