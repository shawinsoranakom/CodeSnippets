def write_model(model_path, huggingface_repo_id="google/timesfm-2.5-200m-pytorch", safe_serialization=True):
    os.makedirs(model_path, exist_ok=True)
    tmp_model_path = os.path.join(model_path, "tmp")
    os.makedirs(tmp_model_path, exist_ok=True)

    checkpoint_path = download_checkpoint_from_hub(huggingface_repo_id)

    # Create model instance and load checkpoint
    tfm = timesfm.TimesFM_2p5_200M_torch()
    tfm.model.load_checkpoint(checkpoint_path)

    # Compile with forecasting configuration
    tfm.compile(
        timesfm.ForecastConfig(
            max_context=1024,
            max_horizon=256,
            normalize_inputs=True,
            use_continuous_quantile_head=True,
        )
    )
    original_model = tfm.model

    # Get actual dimensions from original model
    quantile_output_dims = original_model.output_projection_quantiles.output_layer.weight.shape[0]
    # Original TimesFM 2.5 has 9 quantiles + 1 extra (median/point prediction) = 10 total
    actual_quantile_len = quantile_output_dims // 10  # 9 quantiles + 1 = 10 total

    timesfm_config = TimesFm2_5Config(
        patch_length=32,
        context_length=16384,
        horizon_length=128,
        num_hidden_layers=20,
        hidden_size=1280,
        intermediate_size=1280,
        head_dim=80,
        num_attention_heads=16,
        output_quantile_len=actual_quantile_len,
        decode_index=5,
        use_bias=False,
        activation="swish",
        quantiles=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
        max_position_embeddings=16384,
    )
    timesfm_config.save_pretrained(tmp_model_path)
    timesfm_model = TimesFm2_5ModelForPrediction(timesfm_config)

    # Mapping of the layers from the original TimesFM 2.5 model to the Transformers model
    MODEL_LAYER_MAPPING = {
        # Input projection (tokenizer) - ResidualBlock: 64 -> 1280 -> 1280
        "tokenizer.hidden_layer.weight": "model.input_ff_layer.input_layer.weight",
        "tokenizer.hidden_layer.bias": "model.input_ff_layer.input_layer.bias",
        "tokenizer.output_layer.weight": "model.input_ff_layer.output_layer.weight",
        "tokenizer.output_layer.bias": "model.input_ff_layer.output_layer.bias",
        "tokenizer.residual_layer.weight": "model.input_ff_layer.residual_layer.weight",
        "tokenizer.residual_layer.bias": "model.input_ff_layer.residual_layer.bias",
        # Separate output projections for TimesFM 2.5 - these are at model level, not inside model
        # Point projection: 1280 -> 1280 -> 1280
        "output_projection_point.hidden_layer.weight": "output_projection_point.input_layer.weight",
        "output_projection_point.output_layer.weight": "output_projection_point.output_layer.weight",
        "output_projection_point.residual_layer.weight": "output_projection_point.residual_layer.weight",
        # Quantile projection: 1280 -> 1280 -> output_dims
        "output_projection_quantiles.hidden_layer.weight": "output_projection_quantiles.input_layer.weight",
        "output_projection_quantiles.output_layer.weight": "output_projection_quantiles.output_layer.weight",
        "output_projection_quantiles.residual_layer.weight": "output_projection_quantiles.residual_layer.weight",
    }

    TRANSFORMER_LAYER_MAPPING = {
        # Attention layers - MultiHeadAttention with separate q, k, v projections
        "stacked_xf[{i}].attn.query.weight": "model.layers[{i}].self_attn.q_proj.weight",
        "stacked_xf[{i}].attn.key.weight": "model.layers[{i}].self_attn.k_proj.weight",
        "stacked_xf[{i}].attn.value.weight": "model.layers[{i}].self_attn.v_proj.weight",
        "stacked_xf[{i}].attn.out.weight": "model.layers[{i}].self_attn.o_proj.weight",
        # QK normalization layers (RMS norm) - uses 'scale' instead of 'weight'
        "stacked_xf[{i}].attn.query_ln.scale": "model.layers[{i}].self_attn.q_norm.weight",
        "stacked_xf[{i}].attn.key_ln.scale": "model.layers[{i}].self_attn.k_norm.weight",
        # Per-dimension scaling parameter
        "stacked_xf[{i}].attn.per_dim_scale.per_dim_scale": "model.layers[{i}].self_attn.scaling",
        # MLP layers (feed forward)
        "stacked_xf[{i}].ff0.weight": "model.layers[{i}].mlp.ff0.weight",
        "stacked_xf[{i}].ff1.weight": "model.layers[{i}].mlp.ff1.weight",
        # Layer normalization (RMS norm) - uses 'scale' instead of 'weight'
        "stacked_xf[{i}].pre_attn_ln.scale": "model.layers[{i}].input_layernorm.weight",
        "stacked_xf[{i}].post_attn_ln.scale": "model.layers[{i}].post_attention_layernorm.weight",
        "stacked_xf[{i}].pre_ff_ln.scale": "model.layers[{i}].pre_feedforward_layernorm.weight",
        "stacked_xf[{i}].post_ff_ln.scale": "model.layers[{i}].post_feedforward_layernorm.weight",
    }

    # Debug: Print both model structures
    print(f"Original model attributes: {dir(original_model)}")
    print(f"\\nTransformers model attributes: {dir(timesfm_model)}")
    print(f"\\nTransformers model (inner) attributes: {dir(timesfm_model.model)}")
    print(f"\\nTransformers input_ff_layer attributes: {dir(timesfm_model.model.input_ff_layer)}")

    # Copy model-level weights
    for old_key, new_key in MODEL_LAYER_MAPPING.items():
        try:
            old_attr = get_nested_attr(original_model, old_key)  # Get tensor from original model
            new_attr = get_nested_attr(timesfm_model, new_key)  # Get corresponding attribute in new model

            print(f"Shape comparison {old_key}: {old_attr.shape} vs {new_key}: {new_attr.shape}")

            if old_attr.shape == new_attr.shape:
                new_attr.data.copy_(old_attr.data)  # Copy data
                print(f"✅ Converted {old_key} -> {new_key}")
            else:
                print(f"⚠️  Shape mismatch {old_key}: {old_attr.shape} vs {new_attr.shape}")
        except AttributeError as e:
            print(f"Skipping {old_key}: {e}")

    # Copy transformer layer weights
    num_layers = len(timesfm_model.model.layers)
    for i in range(num_layers):
        # Special handling for fused QKV weights
        try:
            # Check if original model has fused QKV projection
            qkv_fused = get_nested_attr(original_model, f"stacked_xf[{i}].attn.qkv_proj.weight")

            # Split fused QKV into separate Q, K, V projections
            # QKV fused shape: [3 * hidden_size, hidden_size] = [3840, 1280]
            # Split into Q: [1280, 1280], K: [1280, 1280], V: [1280, 1280]
            q_weight, k_weight, v_weight = qkv_fused.chunk(3, dim=0)

            # Copy to separate projections
            q_proj = get_nested_attr(timesfm_model, f"model.layers[{i}].self_attn.q_proj.weight")
            k_proj = get_nested_attr(timesfm_model, f"model.layers[{i}].self_attn.k_proj.weight")
            v_proj = get_nested_attr(timesfm_model, f"model.layers[{i}].self_attn.v_proj.weight")

            q_proj.data.copy_(q_weight.data)
            k_proj.data.copy_(k_weight.data)
            v_proj.data.copy_(v_weight.data)

            if i == 0:
                print(
                    f"✅ Converted layer {i}: stacked_xf[{i}].attn.qkv_proj.weight (fused) -> separate Q/K/V projections"
                )
                print(f"   Q: {q_weight.shape}, K: {k_weight.shape}, V: {v_weight.shape}")
        except AttributeError:
            # No fused QKV, try separate weights
            if i == 0:
                print(f"⚠️  Layer {i}: No fused QKV found, trying separate Q/K/V weights...")

        # Copy all other transformer layer weights
        for old_template, new_template in TRANSFORMER_LAYER_MAPPING.items():
            old_key = old_template.format(i=i)
            new_key = new_template.format(i=i)

            # Skip Q/K/V weights if we already handled fused QKV
            if any(x in old_key for x in [".query.weight", ".key.weight", ".value.weight"]):
                continue

            try:
                # Get tensor from original model
                old_attr = get_nested_attr(original_model, old_key)
                # Get corresponding attribute in new model
                new_attr = get_nested_attr(timesfm_model, new_key)
                new_attr.data.copy_(old_attr.data)  # Copy data
                if i == 0:  # Only print first layer details
                    print(f"✅ Converted layer {i}: {old_key} -> {new_key}")
            except AttributeError:
                if i == 0:  # Only print first layer errors
                    print(f"Skipping layer {i}: {old_key} (not found in original model).")

    timesfm_model.save_pretrained(model_path, safe_serialization=safe_serialization)
    shutil.rmtree(tmp_model_path)
    print(f"✅ Model saved to {model_path}")