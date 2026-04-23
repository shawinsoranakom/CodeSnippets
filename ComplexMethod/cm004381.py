def convert_megatron_checkpoint(args, input_state_dict, config):
    # The converted output model.
    output_state_dict = {}

    # old versions did not store training args
    ds_args = input_state_dict.get("args", None)
    if ds_args is not None:
        # do not make the user write a config file when the exact dimensions/sizes are already in the checkpoint
        # from pprint import pprint
        # pprint(vars(ds_args))

        config.vocab_size = ds_args.padded_vocab_size
        config.n_positions = ds_args.max_position_embeddings
        config.n_embd = ds_args.hidden_size
        config.n_layer = ds_args.num_layers
        config.n_head = ds_args.num_attention_heads
        config.n_inner = ds_args.ffn_hidden_size
        # pprint(config)

    # The number of heads.
    heads = config.n_head
    # The hidden_size per head.
    hidden_size_per_head = config.n_embd // config.n_head
    # Megatron-LM checkpoint version
    if "checkpoint_version" in input_state_dict:
        checkpoint_version = input_state_dict["checkpoint_version"]
    else:
        checkpoint_version = 0.0

    # The model.
    model = input_state_dict["model"]
    # The language model.
    lm = model["language_model"]
    # The embeddings.
    embeddings = lm["embedding"]

    # The word embeddings.
    word_embeddings = embeddings["word_embeddings"]["weight"]
    # Truncate the embedding table to vocab_size rows.
    word_embeddings = word_embeddings[: config.vocab_size, :]
    output_state_dict["transformer.wte.weight"] = word_embeddings

    # The position embeddings.
    pos_embeddings = embeddings["position_embeddings"]["weight"]
    # Read the causal mask dimension (seqlen). [max_sequence_length, hidden_size]
    n_positions = pos_embeddings.size(0)
    if n_positions != config.n_positions:
        raise ValueError(
            f"pos_embeddings.max_sequence_length={n_positions} and config.n_positions={config.n_positions} don't match"
        )
    # Store the position embeddings.
    output_state_dict["transformer.wpe.weight"] = pos_embeddings

    # The transformer.
    transformer = lm["transformer"] if "transformer" in lm else lm["encoder"]

    # The regex to extract layer names.
    layer_re = re.compile(r"layers\.(\d+)\.([a-z0-9_.]+)\.([a-z0-9_]+)")

    # The simple map of names for "automated" rules.
    megatron_to_transformers = {
        "attention.dense": ".attn.c_proj.",
        "self_attention.dense": ".attn.c_proj.",
        "self_attention.proj": ".attn.c_proj.",  # New format
        "mlp.dense_h_to_4h": ".mlp.c_fc.",
        "mlp.dense_4h_to_h": ".mlp.c_proj.",
        "layernorm_mlp.fc1": ".mlp.c_fc.",  # New format
        "layernorm_mlp.fc2": ".mlp.c_proj.",  # New format
    }

    # Extract the layers.
    for key, val in transformer.items():
        # Match the name.
        m = layer_re.match(key)

        # Stop if that's not a layer
        if m is None:
            continue

        # The index of the layer.
        layer_idx = int(m.group(1))
        # The name of the operation.
        op_name = m.group(2)
        # Is it a weight or a bias?
        weight_or_bias = m.group(3)
        # The name of the layer.
        layer_name = f"transformer.h.{layer_idx}"

        # Handle _extra_state keys (skip them)
        if weight_or_bias == "_extra_state":
            continue

        # For layernorm(s), simply store the layer norm.
        if op_name.endswith("layernorm") or weight_or_bias.startswith("layer_norm"):
            if weight_or_bias.startswith("layer_norm"):
                # New format: layers.X.self_attention.layernorm_qkv.layer_norm_weight
                if op_name == "self_attention.layernorm_qkv":
                    ln_name = "ln_1"  # Pre-attention layer norm
                elif op_name == "layernorm_mlp":
                    ln_name = "ln_2"  # Pre-MLP layer norm
                else:
                    ln_name = "ln_1" if op_name.startswith("input") else "ln_2"

                param_name = "weight" if weight_or_bias == "layer_norm_weight" else "bias"
                output_state_dict[layer_name + "." + ln_name + "." + param_name] = val
            else:
                # Old format
                ln_name = "ln_1" if op_name.startswith("input") else "ln_2"
                output_state_dict[layer_name + "." + ln_name + "." + weight_or_bias] = val

        # Handle QKV projections - new format: self_attention.layernorm_qkv.weight/bias
        elif op_name == "self_attention.layernorm_qkv" and weight_or_bias in ["weight", "bias"]:
            if weight_or_bias == "weight":
                # Insert a tensor of 1x1xDxD bias.
                causal_mask = torch.tril(torch.ones((n_positions, n_positions), dtype=torch.float16)).view(
                    1, 1, n_positions, n_positions
                )
                output_state_dict[layer_name + ".attn.bias"] = causal_mask

                # Insert a "dummy" tensor for masked_bias.
                masked_bias = torch.tensor(-1e4, dtype=torch.float16)
                output_state_dict[layer_name + ".attn.masked_bias"] = masked_bias

                out_val = fix_query_key_value_ordering(val, checkpoint_version, 3, heads, hidden_size_per_head)
                # Megatron stores (3*D) x D but transformers-GPT2 expects D x 3*D.
                out_val = out_val.transpose(0, 1).contiguous()
                # Store.
                output_state_dict[layer_name + ".attn.c_attn.weight"] = out_val
            else:  # bias
                out_val = fix_query_key_value_ordering(val, checkpoint_version, 3, heads, hidden_size_per_head)
                # Store. No change of shape.
                output_state_dict[layer_name + ".attn.c_attn.bias"] = out_val

        # Transpose the QKV matrix - old format.
        elif (
            op_name == "attention.query_key_value" or op_name == "self_attention.query_key_value"
        ) and weight_or_bias == "weight":
            # Insert a tensor of 1x1xDxD bias.
            causal_mask = torch.tril(torch.ones((n_positions, n_positions), dtype=torch.float16)).view(
                1, 1, n_positions, n_positions
            )
            output_state_dict[layer_name + ".attn.bias"] = causal_mask

            # Insert a "dummy" tensor for masked_bias.
            masked_bias = torch.tensor(-1e4, dtype=torch.float16)
            output_state_dict[layer_name + ".attn.masked_bias"] = masked_bias

            out_val = fix_query_key_value_ordering(val, checkpoint_version, 3, heads, hidden_size_per_head)
            # Megatron stores (3*D) x D but transformers-GPT2 expects D x 3*D.
            out_val = out_val.transpose(0, 1).contiguous()
            # Store.
            output_state_dict[layer_name + ".attn.c_attn.weight"] = out_val

        # Transpose the bias - old format.
        elif (
            op_name == "attention.query_key_value" or op_name == "self_attention.query_key_value"
        ) and weight_or_bias == "bias":
            out_val = fix_query_key_value_ordering(val, checkpoint_version, 3, heads, hidden_size_per_head)
            # Store. No change of shape.
            output_state_dict[layer_name + ".attn.c_attn.bias"] = out_val

        # Transpose the weights.
        elif weight_or_bias == "weight":
            # DEBUG: Check if op_name exists in the mapping
            if op_name not in megatron_to_transformers:
                continue
            out_name = megatron_to_transformers[op_name]
            output_state_dict[layer_name + out_name + "weight"] = val.transpose(0, 1)

        # Copy the bias.
        elif weight_or_bias == "bias":
            # DEBUG: Check if op_name exists in the mapping
            if op_name not in megatron_to_transformers:
                continue
            out_name = megatron_to_transformers[op_name]
            output_state_dict[layer_name + out_name + "bias"] = val

        # Handle new format MLP weights/biases
        elif weight_or_bias in ["fc1_weight", "fc2_weight", "fc1_bias", "fc2_bias"]:
            if weight_or_bias == "fc1_weight":
                output_state_dict[layer_name + ".mlp.c_fc.weight"] = val.transpose(0, 1)
            elif weight_or_bias == "fc1_bias":
                output_state_dict[layer_name + ".mlp.c_fc.bias"] = val
            elif weight_or_bias == "fc2_weight":
                output_state_dict[layer_name + ".mlp.c_proj.weight"] = val.transpose(0, 1)
            elif weight_or_bias == "fc2_bias":
                output_state_dict[layer_name + ".mlp.c_proj.bias"] = val

        else:
            print(
                f"DEBUG: Unhandled key: {key} (layer {layer_idx}, op_name: '{op_name}', weight_or_bias: '{weight_or_bias}')"
            )

    # DEBUG.
    assert config.n_layer == layer_idx + 1

    # The final layernorm - handle both old and new formats.
    if "final_layernorm.weight" in transformer:
        # Old format
        output_state_dict["transformer.ln_f.weight"] = transformer["final_layernorm.weight"]
        output_state_dict["transformer.ln_f.bias"] = transformer["final_layernorm.bias"]
    elif "final_norm.weight" in transformer:
        # New format
        output_state_dict["transformer.ln_f.weight"] = transformer["final_norm.weight"]
        output_state_dict["transformer.ln_f.bias"] = transformer["final_norm.bias"]
    else:
        print("WARNING: Could not find final layer norm weights!")

    # For LM head, transformers' wants the matrix to weight embeddings.
    output_state_dict["lm_head.weight"] = word_embeddings

    # It should be done!
    return output_state_dict