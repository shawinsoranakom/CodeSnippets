def write_model(
    model_path,
    input_base_path,
    model_size=None,
    llama_version="1",
    vocab_size=None,
    num_shards=None,
    instruct=False,
    push_to_hub=False,
):
    print("Converting the model.")
    params = read_json(os.path.join(input_base_path, "params.json"))
    num_shards = NUM_SHARDS[model_size] if num_shards is None else num_shards
    params = params.get("model", params)
    n_layers = params["n_layers"]
    n_heads = params["n_heads"]
    n_heads_per_shard = n_heads // num_shards
    dim = params["dim"]
    dims_per_head = dim // n_heads
    base = params.get("rope_theta", 10000.0)
    inv_freq = 1.0 / (base ** (torch.arange(0, dims_per_head, 2).float() / dims_per_head))
    if base > 10000.0 and not is_llama_3(llama_version):
        max_position_embeddings = 16384
    else:
        max_position_embeddings = CONTEXT_LENGTH_FOR_VERSION[llama_version]

    if params.get("n_kv_heads", None) is not None:
        num_key_value_heads = params["n_kv_heads"]  # for GQA / MQA
        num_key_value_heads_per_shard = num_key_value_heads // num_shards
        key_value_dim = dims_per_head * num_key_value_heads
    else:  # compatibility with other checkpoints
        num_key_value_heads = n_heads
        num_key_value_heads_per_shard = n_heads_per_shard
        key_value_dim = dim

    # permute for sliced rotary
    def permute(w, n_heads, dim1=dim, dim2=dim):
        return w.view(n_heads, dim1 // n_heads // 2, 2, dim2).transpose(1, 2).reshape(dim1, dim2)

    with tempfile.TemporaryDirectory() as tmp_model_path:
        print(f"Fetching all parameters from the checkpoint at {input_base_path}.")
        # Load weights
        if num_shards == 1:
            # Not sharded
            # (The sharded implementation would also work, but this is simpler.)
            loaded = torch.load(
                os.path.join(input_base_path, "consolidated.00.pth"), map_location="cpu", weights_only=True
            )
        else:
            # Sharded
            checkpoint_list = sorted([file for file in os.listdir(input_base_path) if file.endswith(".pth")])
            print("Loading in order:", checkpoint_list)
            loaded = [
                torch.load(os.path.join(input_base_path, file), map_location="cpu", weights_only=True)
                for file in checkpoint_list
            ]
        param_count = 0
        index_dict = {"weight_map": {}}
        for layer_i in range(n_layers):
            filename = f"pytorch_model-{layer_i + 1}-of-{n_layers + 1}.bin"
            if num_shards == 1:
                # Unsharded
                state_dict = {
                    f"model.layers.{layer_i}.self_attn.q_proj.weight": permute(
                        loaded[f"layers.{layer_i}.attention.wq.weight"], n_heads=n_heads
                    ),
                    f"model.layers.{layer_i}.self_attn.k_proj.weight": permute(
                        loaded[f"layers.{layer_i}.attention.wk.weight"],
                        n_heads=num_key_value_heads,
                        dim1=key_value_dim,
                    ),
                    f"model.layers.{layer_i}.self_attn.v_proj.weight": loaded[f"layers.{layer_i}.attention.wv.weight"],
                    f"model.layers.{layer_i}.self_attn.o_proj.weight": loaded[f"layers.{layer_i}.attention.wo.weight"],
                    f"model.layers.{layer_i}.mlp.gate_proj.weight": loaded[f"layers.{layer_i}.feed_forward.w1.weight"],
                    f"model.layers.{layer_i}.mlp.down_proj.weight": loaded[f"layers.{layer_i}.feed_forward.w2.weight"],
                    f"model.layers.{layer_i}.mlp.up_proj.weight": loaded[f"layers.{layer_i}.feed_forward.w3.weight"],
                    f"model.layers.{layer_i}.input_layernorm.weight": loaded[
                        f"layers.{layer_i}.attention_norm.weight"
                    ],
                    f"model.layers.{layer_i}.post_attention_layernorm.weight": loaded[
                        f"layers.{layer_i}.ffn_norm.weight"
                    ],
                }
            else:
                # Sharded
                # Note that attention.w{q,k,v,o}, feed_fordward.w[1,2,3], attention_norm.weight and ffn_norm.weight share
                # the same storage object, saving attention_norm and ffn_norm will save other weights too, which is
                # redundant as other weights will be stitched from multiple shards. To avoid that, they are cloned.

                state_dict = {
                    f"model.layers.{layer_i}.input_layernorm.weight": loaded[0][
                        f"layers.{layer_i}.attention_norm.weight"
                    ].clone(),
                    f"model.layers.{layer_i}.post_attention_layernorm.weight": loaded[0][
                        f"layers.{layer_i}.ffn_norm.weight"
                    ].clone(),
                }
                state_dict[f"model.layers.{layer_i}.self_attn.q_proj.weight"] = permute(
                    torch.cat(
                        [
                            loaded[i][f"layers.{layer_i}.attention.wq.weight"].view(
                                n_heads_per_shard, dims_per_head, dim
                            )
                            for i in range(len(loaded))
                        ],
                        dim=0,
                    ).reshape(dim, dim),
                    n_heads=n_heads,
                )
                state_dict[f"model.layers.{layer_i}.self_attn.k_proj.weight"] = permute(
                    torch.cat(
                        [
                            loaded[i][f"layers.{layer_i}.attention.wk.weight"].view(
                                num_key_value_heads_per_shard, dims_per_head, dim
                            )
                            for i in range(len(loaded))
                        ],
                        dim=0,
                    ).reshape(key_value_dim, dim),
                    num_key_value_heads,
                    key_value_dim,
                    dim,
                )
                state_dict[f"model.layers.{layer_i}.self_attn.v_proj.weight"] = torch.cat(
                    [
                        loaded[i][f"layers.{layer_i}.attention.wv.weight"].view(
                            num_key_value_heads_per_shard, dims_per_head, dim
                        )
                        for i in range(len(loaded))
                    ],
                    dim=0,
                ).reshape(key_value_dim, dim)

                state_dict[f"model.layers.{layer_i}.self_attn.o_proj.weight"] = torch.cat(
                    [loaded[i][f"layers.{layer_i}.attention.wo.weight"] for i in range(len(loaded))], dim=1
                )
                state_dict[f"model.layers.{layer_i}.mlp.gate_proj.weight"] = torch.cat(
                    [loaded[i][f"layers.{layer_i}.feed_forward.w1.weight"] for i in range(len(loaded))], dim=0
                )
                state_dict[f"model.layers.{layer_i}.mlp.down_proj.weight"] = torch.cat(
                    [loaded[i][f"layers.{layer_i}.feed_forward.w2.weight"] for i in range(len(loaded))], dim=1
                )
                state_dict[f"model.layers.{layer_i}.mlp.up_proj.weight"] = torch.cat(
                    [loaded[i][f"layers.{layer_i}.feed_forward.w3.weight"] for i in range(len(loaded))], dim=0
                )

            state_dict[f"model.layers.{layer_i}.self_attn.rotary_emb.inv_freq"] = inv_freq
            for k, v in state_dict.items():
                index_dict["weight_map"][k] = filename
                param_count += v.numel()
            torch.save(state_dict, os.path.join(tmp_model_path, filename))

        filename = f"pytorch_model-{n_layers + 1}-of-{n_layers + 1}.bin"
        if num_shards == 1:
            # Unsharded
            state_dict = {
                "model.embed_tokens.weight": loaded["tok_embeddings.weight"],
                "model.norm.weight": loaded["norm.weight"],
                "lm_head.weight": loaded["output.weight"],
            }
        else:
            concat_dim = 0 if is_llama_3(llama_version) else 1
            state_dict = {
                "model.norm.weight": loaded[0]["norm.weight"],
                "model.embed_tokens.weight": torch.cat(
                    [loaded[i]["tok_embeddings.weight"] for i in range(len(loaded))], dim=concat_dim
                ),
                "lm_head.weight": torch.cat([loaded[i]["output.weight"] for i in range(len(loaded))], dim=0),
            }

        for k, v in state_dict.items():
            index_dict["weight_map"][k] = filename
            param_count += v.numel()
        torch.save(state_dict, os.path.join(tmp_model_path, filename))

        # Write configs
        index_dict["metadata"] = {"total_size": param_count * 2}
        write_json(index_dict, os.path.join(tmp_model_path, "pytorch_model.bin.index.json"))
        ffn_dim_multiplier = params.get("ffn_dim_multiplier", 1)
        multiple_of = params.get("multiple_of", 256)

        if is_llama_3(llama_version):
            bos_token_id = 128000

            if instruct:
                eos_token_id = [128001, 128008, 128009]
            else:
                eos_token_id = 128001
        else:
            bos_token_id = 1
            eos_token_id = 2

        if llama_version in ["3.1", "3.2", "Guard-3"]:
            rope_parameters = {
                "factor": 32.0 if llama_version == "3.2" else 8.0,
                "low_freq_factor": 1.0,
                "high_freq_factor": 4.0,
                "original_max_position_embeddings": 8192,
                "rope_type": "llama3",
            }
        else:
            rope_parameters = None

        config = LlamaConfig(
            hidden_size=dim,
            intermediate_size=compute_intermediate_size(dim, ffn_dim_multiplier, multiple_of),
            num_attention_heads=params["n_heads"],
            num_hidden_layers=params["n_layers"],
            rms_norm_eps=params["norm_eps"],
            num_key_value_heads=num_key_value_heads,
            vocab_size=vocab_size,
            rope_theta=base,
            rope_parameters=rope_parameters,
            max_position_embeddings=max_position_embeddings,
            bos_token_id=bos_token_id,
            eos_token_id=eos_token_id,
            tie_word_embeddings=llama_version == "3.2",
        )

        config.save_pretrained(tmp_model_path)

        generation_config = GenerationConfig(
            do_sample=True,
            temperature=0.6,
            top_p=0.9,
            bos_token_id=bos_token_id,
            eos_token_id=eos_token_id,
        )
        generation_config.save_pretrained(tmp_model_path)

        # Make space so we can load the model properly now.
        del state_dict
        del loaded
        gc.collect()

        print("Loading the checkpoint in a Llama model.")
        model = LlamaForCausalLM.from_pretrained(tmp_model_path, dtype=torch.bfloat16)

        # Avoid saving this as part of the config.
        del model.config._name_or_path
        model.config.dtype = torch.float16

        print("Saving in the Transformers format.")
        if push_to_hub:
            print("Pushing to the hub.")
            model_name = model_path.split(os.path.sep)[-1]
            model.push_to_hub(model_name, private=True)
        else:
            print("Saving to disk.")
            model.save_pretrained(model_path)