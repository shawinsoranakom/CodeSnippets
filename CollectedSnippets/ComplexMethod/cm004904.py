def write_model(model_path, huggingface_repo_id="google/timesfm-2.0-500m-pytorch"):
    os.makedirs(model_path, exist_ok=True)
    tmp_model_path = os.path.join(model_path, "tmp")
    os.makedirs(tmp_model_path, exist_ok=True)

    tfm = timesfm.TimesFm(
        hparams=timesfm.TimesFmHparams(
            backend="cuda" if torch.cuda.is_available() else "cpu",
            per_core_batch_size=32,
            horizon_len=128,
            input_patch_len=32,
            output_patch_len=128,
            num_layers=50,
            model_dims=1280,
            use_positional_embedding=False,
            context_len=2048,
        ),
        checkpoint=timesfm.TimesFmCheckpoint(huggingface_repo_id=huggingface_repo_id),
    )

    timesfm_config = TimesFmConfig(
        patch_length=tfm.hparams.input_patch_len,
        context_length=tfm.hparams.context_len,
        horizon_length=tfm.hparams.horizon_len,
        num_hidden_layers=tfm.hparams.num_layers,
        hidden_size=tfm.hparams.model_dims,
        intermediate_size=tfm.hparams.model_dims,
        head_dim=tfm.hparams.model_dims // tfm.hparams.num_heads,
        num_attention_heads=tfm.hparams.num_heads,
        use_positional_embedding=tfm.hparams.use_positional_embedding,
    )
    timesfm_config.save_pretrained(tmp_model_path)
    timesfm_model = TimesFmModelForPrediction(timesfm_config)

    # copy the weights from the original model to the new model making
    original_model = tfm._model

    # mapping of the layers from the original model to the transformer model
    MODEL_LAYER_MAPPING = {
        "input_ff_layer.hidden_layer[0].weight": "decoder.input_ff_layer.input_layer.weight",
        "input_ff_layer.hidden_layer[0].bias": "decoder.input_ff_layer.input_layer.bias",
        "input_ff_layer.output_layer.weight": "decoder.input_ff_layer.output_layer.weight",
        "input_ff_layer.output_layer.bias": "decoder.input_ff_layer.output_layer.bias",
        "input_ff_layer.residual_layer.weight": "decoder.input_ff_layer.residual_layer.weight",
        "input_ff_layer.residual_layer.bias": "decoder.input_ff_layer.residual_layer.bias",
        "freq_emb.weight": "decoder.freq_emb.weight",
        "horizon_ff_layer.hidden_layer[0].weight": "horizon_ff_layer.input_layer.weight",
        "horizon_ff_layer.hidden_layer[0].bias": "horizon_ff_layer.input_layer.bias",
        "horizon_ff_layer.output_layer.weight": "horizon_ff_layer.output_layer.weight",
        "horizon_ff_layer.output_layer.bias": "horizon_ff_layer.output_layer.bias",
        "horizon_ff_layer.residual_layer.weight": "horizon_ff_layer.residual_layer.weight",
        "horizon_ff_layer.residual_layer.bias": "horizon_ff_layer.residual_layer.bias",
    }

    TRANSFORMER_LAYER_MAPPING = {
        "stacked_transformer.layers[{i}].self_attn.qkv_proj.weight": "decoder.layers[{i}].self_attn.qkv_proj.weight",
        "stacked_transformer.layers[{i}].self_attn.qkv_proj.bias": "decoder.layers[{i}].self_attn.qkv_proj.bias",
        "stacked_transformer.layers[{i}].self_attn.o_proj.weight": "decoder.layers[{i}].self_attn.o_proj.weight",
        "stacked_transformer.layers[{i}].self_attn.o_proj.bias": "decoder.layers[{i}].self_attn.o_proj.bias",
        "stacked_transformer.layers[{i}].self_attn.scaling": "decoder.layers[{i}].self_attn.scaling",
        "stacked_transformer.layers[{i}].mlp.gate_proj.weight": "decoder.layers[{i}].mlp.gate_proj.weight",
        "stacked_transformer.layers[{i}].mlp.gate_proj.bias": "decoder.layers[{i}].mlp.gate_proj.bias",
        "stacked_transformer.layers[{i}].mlp.down_proj.weight": "decoder.layers[{i}].mlp.down_proj.weight",
        "stacked_transformer.layers[{i}].mlp.down_proj.bias": "decoder.layers[{i}].mlp.down_proj.bias",
        "stacked_transformer.layers[{i}].mlp.layer_norm.weight": "decoder.layers[{i}].mlp.layer_norm.weight",
        "stacked_transformer.layers[{i}].mlp.layer_norm.bias": "decoder.layers[{i}].mlp.layer_norm.bias",
        "stacked_transformer.layers[{i}].input_layernorm.weight": "decoder.layers[{i}].input_layernorm.weight",
    }

    for old_key, new_key in MODEL_LAYER_MAPPING.items():
        try:
            old_attr = get_nested_attr(original_model, old_key)  # Get tensor from original model
            new_attr = get_nested_attr(timesfm_model, new_key)  # Get corresponding attribute in new model
            new_attr.data.copy_(old_attr.data)  # Copy data
        except AttributeError:
            print(f"Skipping {old_key} (not found in original model).")

    num_layers = len(timesfm_model.decoder.layers)
    for i in range(num_layers):
        for old_template, new_template in TRANSFORMER_LAYER_MAPPING.items():
            old_key = old_template.format(i=i)
            new_key = new_template.format(i=i)

            try:
                # Get tensor from original model
                old_attr = get_nested_attr(original_model, old_key)
                if "qkv_proj" in old_key:
                    # Split the tensor into q, k, v projections
                    q_proj, k_proj, v_proj = (
                        old_attr[: tfm.hparams.model_dims, ...],
                        old_attr[tfm.hparams.model_dims : tfm.hparams.model_dims * 2, ...],
                        old_attr[tfm.hparams.model_dims * 2 :, ...],
                    )
                    # Get corresponding attribute in new model
                    q_key = new_key.replace("qkv_proj", "q_proj")
                    q_attr = get_nested_attr(timesfm_model, q_key)
                    q_attr.data.copy_(q_proj.data)  # Copy data
                    k_key = new_key.replace("qkv_proj", "k_proj")
                    k_attr = get_nested_attr(timesfm_model, k_key)
                    k_attr.data.copy_(k_proj.data)  # Copy data
                    v_key = new_key.replace("qkv_proj", "v_proj")
                    v_attr = get_nested_attr(timesfm_model, v_key)
                    v_attr.data.copy_(v_proj.data)  # Copy data
                else:
                    # Get corresponding attribute in new model
                    new_attr = get_nested_attr(timesfm_model, new_key)
                    new_attr.data.copy_(old_attr.data)  # Copy data
            except AttributeError:
                print(f"Skipping {old_key} (not found in original model).")

    timesfm_model.save_pretrained(model_path)
    shutil.rmtree(tmp_model_path)