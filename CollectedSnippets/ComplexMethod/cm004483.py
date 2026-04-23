def write_model(
    model_path,
    input_base_path,
    params,
    image_token_id,
    tokenizer=None,
    num_shards=None,
    push_to_hub=False,
):
    print("Converting the model.")
    num_shards = 1
    model_params = params.get("model", params)
    n_layers = model_params["n_layers"]
    n_heads = model_params["n_heads"]
    dim = model_params["dim"]
    dims_per_head = dim // n_heads
    base = model_params.get("rope_theta", 10000.0)
    inv_freq = 1.0 / (base ** (torch.arange(0, dims_per_head, 2).float() / dims_per_head))
    context_length = model_params["max_seqlen"]
    max_position_embeddings = context_length
    tie_word_embeddings = model_params.get("weight_tying", False)
    projector_pooling_ratio = model_params.get("pooling_ratio", 1)

    if model_params.get("n_kv_heads", None) is not None:
        num_key_value_heads = model_params["n_kv_heads"]  # for GQA / MQA
        key_value_dim = dims_per_head * num_key_value_heads
    else:  # compatibility with other checkpoints
        num_key_value_heads = n_heads
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
                os.path.join(input_base_path, "consolidated.pth"),
                map_location="cpu",
                weights_only=True,
            )
        else:
            # Sharded
            checkpoint_list = sorted([file for file in os.listdir(input_base_path) if file.endswith(".pth")])
            print("Loading in order:", checkpoint_list)
            loaded = [
                torch.load(
                    os.path.join(input_base_path, file),
                    map_location="cpu",
                    weights_only=True,
                )
                for file in checkpoint_list
            ]
        param_count = 0
        index_dict = {"weight_map": {}}
        for layer_i in range(n_layers):
            filename = f"pytorch_model-{layer_i + 1}-of-{n_layers + 2}.bin"
            assert num_shards == 1, "PerceptionLM does not support sharded weights"
            state_dict = {
                f"model.language_model.layers.{layer_i}.self_attn.q_proj.weight": permute(
                    loaded[f"layers.{layer_i}.attention.wq.weight"], n_heads=n_heads
                ),
                f"model.language_model.layers.{layer_i}.self_attn.k_proj.weight": permute(
                    loaded[f"layers.{layer_i}.attention.wk.weight"],
                    n_heads=num_key_value_heads,
                    dim1=key_value_dim,
                ),
                f"model.language_model.layers.{layer_i}.self_attn.v_proj.weight": loaded[
                    f"layers.{layer_i}.attention.wv.weight"
                ],
                f"model.language_model.layers.{layer_i}.self_attn.o_proj.weight": loaded[
                    f"layers.{layer_i}.attention.wo.weight"
                ],
                f"model.language_model.layers.{layer_i}.mlp.gate_proj.weight": loaded[
                    f"layers.{layer_i}.feed_forward.w1.weight"
                ],
                f"model.language_model.layers.{layer_i}.mlp.down_proj.weight": loaded[
                    f"layers.{layer_i}.feed_forward.w2.weight"
                ],
                f"model.language_model.layers.{layer_i}.mlp.up_proj.weight": loaded[
                    f"layers.{layer_i}.feed_forward.w3.weight"
                ],
                f"model.language_model.layers.{layer_i}.input_layernorm.weight": loaded[
                    f"layers.{layer_i}.attention_norm.weight"
                ],
                f"model.language_model.layers.{layer_i}.post_attention_layernorm.weight": loaded[
                    f"layers.{layer_i}.ffn_norm.weight"
                ],
            }
            state_dict[f"model.language_model.layers.{layer_i}.self_attn.rotary_emb.inv_freq"] = inv_freq
            for k, v in state_dict.items():
                index_dict["weight_map"][k] = filename
                param_count += v.numel()
            torch.save(state_dict, os.path.join(tmp_model_path, filename))
            print(f"Saved {filename}")

        filename = f"pytorch_model-{n_layers + 1}-of-{n_layers + 2}.bin"

        state_dict = {
            "model.language_model.embed_tokens.weight": loaded["tok_embeddings.weight"],
            "model.language_model.norm.weight": loaded["norm.weight"],
            "model.multi_modal_projector.linear_1.weight": loaded["vision_projector.projector.0.weight"],
            "model.multi_modal_projector.linear_2.weight": loaded["vision_projector.projector.2.weight"],
            "model.multi_modal_projector.linear_1.bias": loaded["vision_projector.projector.0.bias"],
            "model.multi_modal_projector.linear_2.bias": loaded["vision_projector.projector.2.bias"],
        }
        if not tie_word_embeddings:
            state_dict["lm_head.weight"] = loaded["output.weight"]
        for k, v in state_dict.items():
            index_dict["weight_map"][k] = filename
            param_count += v.numel()
        torch.save(state_dict, os.path.join(tmp_model_path, filename))
        print(f"Saved {filename}")

        filename = f"pytorch_model-{n_layers + 2}-of-{n_layers + 2}.bin"
        state_dict = {k.replace("vision_model.", ""): v for k, v in loaded.items() if "vision_model" in k}
        vision_params = model_params["vision_model"]
        if vision_params["layers"] == 23 and vision_params["width"] == 1024:
            architecture = "vit_pe_core_large_patch14_336"
        elif vision_params["layers"] == 47 and vision_params["width"] == 1536:
            architecture = "vit_pe_core_gigantic_patch14_448"
        else:
            raise ValueError(
                f"Unsupported PE config: {vision_params['layers']} layers and {vision_params['width']} width"
            )

        vision_config = TimmWrapperConfig.from_pretrained(
            f"timm/{architecture}.fb",
            model_args={
                "embed_dim": vision_params["width"],
                "depth": vision_params["layers"],
                "img_size": (vision_params["image_size"], vision_params["image_size"]),
                "global_pool": "",
                "use_post_transformer_norm": vision_params["use_ln_post"],
                "init_values": vision_params["ls_init_value"],
                "ref_feat_shape": (
                    vision_params["image_size"] // vision_params["patch_size"],
                    vision_params["image_size"] // vision_params["patch_size"],
                ),
            },
        )

        perception_encoder = AutoModel.from_config(vision_config)
        state_dict = checkpoint_filter_fn(state_dict, perception_encoder)
        state_dict = {"model.vision_tower.timm_model." + k: v for k, v in state_dict.items()}
        for k, v in state_dict.items():
            index_dict["weight_map"][k] = filename
            param_count += v.numel()
        torch.save(state_dict, os.path.join(tmp_model_path, filename))
        print(f"Saved {filename}")

        # Write configs
        index_dict["metadata"] = {"total_size": param_count * 2}
        write_json(index_dict, os.path.join(tmp_model_path, "pytorch_model.bin.index.json"))
        ffn_dim_multiplier = model_params.get("ffn_dim_multiplier", 1)
        multiple_of = model_params.get("multiple_of", 256)

        bos_token_id = tokenizer.convert_tokens_to_ids("<|begin_of_text|>")
        eos_token_id = [tokenizer.convert_tokens_to_ids(t) for t in ["<|end_of_text|>", "<|eot_id|>"]]

        use_scaled_rope = model_params["use_scaled_rope"]
        if use_scaled_rope:
            rope_parameters = {
                "factor": model_params["rope_scale_factor"] * 1.0,
                "low_freq_factor": model_params.get("low_freq_factor", 1.0) * 1.0,
                "high_freq_factor": model_params.get("high_freq_factor", 4.0) * 1.0,
                "original_max_position_embeddings": 8192,
                "rope_type": "llama3",
            }
        else:
            rope_parameters = None

        text_config = LlamaConfig(
            hidden_size=dim,
            intermediate_size=compute_intermediate_size(dim, ffn_dim_multiplier, multiple_of),
            num_attention_heads=model_params["n_heads"],
            num_hidden_layers=model_params["n_layers"],
            rms_norm_eps=model_params["norm_eps"],
            num_key_value_heads=num_key_value_heads,
            vocab_size=len(tokenizer),
            rope_theta=base,
            rope_parameters=rope_parameters,
            max_position_embeddings=max_position_embeddings,
            bos_token_id=bos_token_id,
            eos_token_id=eos_token_id,
            tie_word_embeddings=tie_word_embeddings,
        )

        config = PerceptionLMConfig(
            text_config=text_config.to_dict(),
            vision_config=vision_config.to_dict(),
            projector_pooling_ratio=projector_pooling_ratio,
            vision_use_cls_token=vision_params["use_cls_token"],
            image_token_id=tokenizer.image_token_id,
            video_token_id=tokenizer.video_token_id,
        )

        config.save_pretrained(tmp_model_path)

        generation_config = GenerationConfig(
            do_sample=False,
            bos_token_id=bos_token_id,
            eos_token_id=eos_token_id,
        )
        generation_config.save_pretrained(tmp_model_path)

        # Make space so we can load the model properly now.
        del state_dict
        # output_weight = loaded.get("output.weight", None)
        del loaded
        gc.collect()

        print("Loading the checkpoint in a PerceptionLM model.")
        model = PerceptionLMForConditionalGeneration.from_pretrained(
            tmp_model_path, dtype=torch.bfloat16, low_cpu_mem_usage=True
        )
        # if not tie_word_embeddings:
        #     if output_weight is None:
        #         raise ValueError("Output weight/lm_head is not found in the checkpoint.")
        #     model.lm_head.load_state_dict({"weight": output_weight})

        # Avoid saving this as part of the config.
        del model.config._name_or_path
        model.config.dtype = torch.bfloat16

        print("Saving in the Transformers format.")
        model_name = model_path.split(os.path.sep)[-1]
        if push_to_hub:
            print("Pushing to the hub.")
            model.push_to_hub(model_name, private=True)
        else:
            print("Saving to disk.")
            model.save_pretrained(model_name)