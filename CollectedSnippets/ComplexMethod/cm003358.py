def convert(input_nemo_file, output_hf_file, precision=None, cpu_only=False) -> None:
    """
    Convert NeMo weights to HF weights
    """
    dummy_trainer = Trainer(devices=1, accelerator="cpu", strategy=NLPDDPStrategy())
    model_config = MegatronGPTModel.restore_from(input_nemo_file, trainer=dummy_trainer, return_config=True)
    model_config.tensor_model_parallel_size = 1
    model_config.pipeline_model_parallel_size = 1
    model_config.sequence_parallel = False
    model_config.transformer_engine = True
    if cpu_only:
        map_location = torch.device("cpu")
        model_config.use_cpu_initialization = True
        model_config.dist_ckpt_load_on_device = False
    else:
        map_location = None

    if cpu_only:
        logging.info("******** Loading model on CPU. This will take a significant amount of time.")

    model = MegatronGPTModel.restore_from(
        input_nemo_file, trainer=dummy_trainer, override_config_path=model_config, map_location=map_location
    )

    vocab_size = model.padded_vocab_size

    if precision is None:
        precision = model.cfg.precision
    if precision in [32, "32"]:
        dtype = torch.float32
    elif precision in [16, "16", "16-mixed"]:
        dtype = torch.float16
    elif precision in ["bf16", "bf16-mixed"]:
        dtype = torch.bfloat16
    else:
        logging.warning(f"Precision string {precision} is not recognized, falling back to fp32")
        dtype = torch.float32  # fallback
    logging.info(f"Using precision {dtype}")

    def param_to_weights(param):
        return param.to(dtype)

    checkpoint = OrderedDict()

    hidden_size = model.cfg.hidden_size
    head_num = model.cfg.num_attention_heads
    num_layers = model.cfg.num_layers
    ffn_hidden_size = model.cfg.ffn_hidden_size
    num_query_groups = model.cfg.get("num_query_groups", head_num)  # different num_query_groups for 70B
    if num_query_groups is None:
        num_query_groups = head_num
    heads_per_group = head_num // num_query_groups
    qkv_total_dim = head_num + 2 * num_query_groups

    # Embedding
    embed_weight = model.state_dict()["model.embedding.word_embeddings.weight"]
    embed_weights_base_name = "model.embed_tokens.weight"
    checkpoint[embed_weights_base_name] = param_to_weights(embed_weight)

    for l in range(int(num_layers)):
        print(f"converting layer {l}")

        qkv_weights = model.state_dict()[f"model.decoder.layers.{l}.self_attention.linear_qkv.weight"]
        qkv_weights = qkv_weights.reshape([qkv_total_dim, -1, hidden_size])

        q_slice = torch.cat(
            [
                torch.arange((heads_per_group + 2) * i, (heads_per_group + 2) * i + heads_per_group)
                for i in range(num_query_groups)
            ]
        )
        k_slice = torch.arange(heads_per_group, qkv_total_dim, (heads_per_group + 2))
        v_slice = torch.arange(heads_per_group + 1, qkv_total_dim, (heads_per_group + 2))
        ## Example of slices
        ## (without GQA): num_query_groups = head_num = 32,
        ## q_slice = [0, 3, 6, 9 , ... 90, 93]
        ## k_slice = [1, 4, 7, 10, ... 91, 94]
        ## v_slice = [2, 5, 8, 11, ... 92, 95]
        ## (with GQA): num_query_groups = 8, head_num = 64
        ## q_slice = [0, 1, .. 6, 7, 10, 11, .. 16, 17, 20, 21, .. 67, 70, ... 76, 77]
        ## k_slice = [8, 18, 28, ... 68, 78]
        ## v_slice = [9, 19, 29, ... 69, 79]

        q_weights_base_name = f"model.layers.{l}.self_attn.q_proj.weight"
        k_weights_base_name = f"model.layers.{l}.self_attn.k_proj.weight"
        v_weights_base_name = f"model.layers.{l}.self_attn.v_proj.weight"

        checkpoint[q_weights_base_name] = param_to_weights(qkv_weights[q_slice].reshape(-1, hidden_size))
        checkpoint[k_weights_base_name] = param_to_weights(qkv_weights[k_slice].reshape(-1, hidden_size))
        checkpoint[v_weights_base_name] = param_to_weights(qkv_weights[v_slice].reshape(-1, hidden_size))

        # attention dense
        o_weight = model.state_dict()[f"model.decoder.layers.{l}.self_attention.linear_proj.weight"]
        o_weight_base_name = f"model.layers.{l}.self_attn.o_proj.weight"
        checkpoint[o_weight_base_name] = param_to_weights(o_weight)

        # mlp
        mlp_weights = model.state_dict()[f"model.decoder.layers.{l}.mlp.linear_fc1.weight"]
        mlp_up_proj_weight = model.state_dict()[f"model.decoder.layers.{l}.mlp.linear_fc2.weight"]

        if mlp_weights.shape[0] != mlp_up_proj_weight.shape[1]:
            # Has projection (used for swi-glu)
            logging.warning(
                "Gated projection layers detected in NeMo checkpoint. Currently Nemotron HF does not support gated MLP."
            )
            assert mlp_weights.shape[0] == 2 * mlp_up_proj_weight.shape[1]

            mlp_down_proj_weight = mlp_weights[:ffn_hidden_size, :]
            mlp_gate_proj_weight = mlp_weights[ffn_hidden_size:, :]

            mlp_down_proj_base_name = f"model.layers.{l}.mlp.gate_proj.weight"
            mlp_gate_proj_base_name = f"model.layers.{l}.mlp.up_proj.weight"

            checkpoint[mlp_down_proj_base_name] = param_to_weights(mlp_down_proj_weight)
            checkpoint[mlp_gate_proj_base_name] = param_to_weights(mlp_gate_proj_weight)
        else:
            mlp_down_proj_weight = mlp_weights
            mlp_down_proj_base_name = f"model.layers.{l}.mlp.up_proj.weight"
            checkpoint[mlp_down_proj_base_name] = param_to_weights(mlp_down_proj_weight)

        mlp_up_proj_base_name = f"model.layers.{l}.mlp.down_proj.weight"
        checkpoint[mlp_up_proj_base_name] = param_to_weights(mlp_up_proj_weight)

        # layernorm
        input_ln_weight = model.state_dict()[f"model.decoder.layers.{l}.self_attention.linear_qkv.layer_norm_weight"]
        input_ln_base_name = f"model.layers.{l}.input_layernorm.weight"
        checkpoint[input_ln_base_name] = param_to_weights(input_ln_weight)
        if (
            model.state_dict().get(f"model.decoder.layers.{l}.self_attention.linear_qkv.layer_norm_bias", None)
            is not None
        ):
            input_ln_bias = model.state_dict()[f"model.decoder.layers.{l}.self_attention.linear_qkv.layer_norm_bias"]
            input_ln_bias_name = f"model.layers.{l}.input_layernorm.bias"
            checkpoint[input_ln_bias_name] = param_to_weights(input_ln_bias)

        post_attn_ln_weight = model.state_dict()[f"model.decoder.layers.{l}.mlp.linear_fc1.layer_norm_weight"]
        post_attn_ln_base_name = f"model.layers.{l}.post_attention_layernorm.weight"
        checkpoint[post_attn_ln_base_name] = param_to_weights(post_attn_ln_weight)
        if model.state_dict().get(f"model.decoder.layers.{l}.mlp.linear_fc1.layer_norm_bias", None) is not None:
            post_attn_ln_bias = model.state_dict()[f"model.decoder.layers.{l}.mlp.linear_fc1.layer_norm_bias"]
            post_attn_ln_bias_name = f"model.layers.{l}.post_attention_layernorm.bias"
            checkpoint[post_attn_ln_bias_name] = param_to_weights(post_attn_ln_bias)

        print(f"done layer {l}")

    final_ln_weight = model.state_dict()["model.decoder.final_layernorm.weight"]
    final_ln_base_name = "model.norm.weight"
    checkpoint[final_ln_base_name] = param_to_weights(final_ln_weight)
    if model.state_dict().get("model.decoder.final_layernorm.bias", None) is not None:
        final_ln_bias = model.state_dict()["model.decoder.final_layernorm.bias"]
        final_ln_bias_name = "model.norm.bias"
        checkpoint[final_ln_bias_name] = param_to_weights(final_ln_bias)

    output_layer_weight = model.state_dict()["model.output_layer.weight"]
    output_layer_base_name = "lm_head.weight"
    checkpoint[output_layer_base_name] = param_to_weights(output_layer_weight)

    os.makedirs(os.path.dirname(output_hf_file), exist_ok=True)
    torch.save(checkpoint, output_hf_file)
    logging.info(f"Weights saved to {output_hf_file}")

    return model_config, model.tokenizer, dtype, vocab_size