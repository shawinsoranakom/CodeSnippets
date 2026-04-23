def flux_to_diffusers(mmdit_config, output_prefix=""):
    n_double_layers = mmdit_config.get("depth", 0)
    n_single_layers = mmdit_config.get("depth_single_blocks", 0)
    hidden_size = mmdit_config.get("hidden_size", 0)

    key_map = {}
    for index in range(n_double_layers):
        prefix_from = "transformer_blocks.{}".format(index)
        prefix_to = "{}double_blocks.{}".format(output_prefix, index)

        for end in ("weight", "bias"):
            k = "{}.attn.".format(prefix_from)
            qkv = "{}.img_attn.qkv.{}".format(prefix_to, end)
            key_map["{}to_q.{}".format(k, end)] = (qkv, (0, 0, hidden_size))
            key_map["{}to_k.{}".format(k, end)] = (qkv, (0, hidden_size, hidden_size))
            key_map["{}to_v.{}".format(k, end)] = (qkv, (0, hidden_size * 2, hidden_size))

            k = "{}.attn.".format(prefix_from)
            qkv = "{}.txt_attn.qkv.{}".format(prefix_to, end)
            key_map["{}add_q_proj.{}".format(k, end)] = (qkv, (0, 0, hidden_size))
            key_map["{}add_k_proj.{}".format(k, end)] = (qkv, (0, hidden_size, hidden_size))
            key_map["{}add_v_proj.{}".format(k, end)] = (qkv, (0, hidden_size * 2, hidden_size))

        block_map = {
                        "attn.to_out.0.weight": "img_attn.proj.weight",
                        "attn.to_out.0.bias": "img_attn.proj.bias",
                        "norm1.linear.weight": "img_mod.lin.weight",
                        "norm1.linear.bias": "img_mod.lin.bias",
                        "norm1_context.linear.weight": "txt_mod.lin.weight",
                        "norm1_context.linear.bias": "txt_mod.lin.bias",
                        "attn.to_add_out.weight": "txt_attn.proj.weight",
                        "attn.to_add_out.bias": "txt_attn.proj.bias",
                        "ff.net.0.proj.weight": "img_mlp.0.weight",
                        "ff.net.0.proj.bias": "img_mlp.0.bias",
                        "ff.net.2.weight": "img_mlp.2.weight",
                        "ff.net.2.bias": "img_mlp.2.bias",
                        "ff_context.net.0.proj.weight": "txt_mlp.0.weight",
                        "ff_context.net.0.proj.bias": "txt_mlp.0.bias",
                        "ff_context.net.2.weight": "txt_mlp.2.weight",
                        "ff_context.net.2.bias": "txt_mlp.2.bias",
                        "ff.linear_in.weight": "img_mlp.0.weight",  # LyCoris LoKr
                        "ff.linear_in.bias": "img_mlp.0.bias",
                        "ff.linear_out.weight": "img_mlp.2.weight",
                        "ff.linear_out.bias": "img_mlp.2.bias",
                        "ff_context.linear_in.weight": "txt_mlp.0.weight",
                        "ff_context.linear_in.bias": "txt_mlp.0.bias",
                        "ff_context.linear_out.weight": "txt_mlp.2.weight",
                        "ff_context.linear_out.bias": "txt_mlp.2.bias",
                        "attn.norm_q.weight": "img_attn.norm.query_norm.weight",
                        "attn.norm_k.weight": "img_attn.norm.key_norm.weight",
                        "attn.norm_added_q.weight": "txt_attn.norm.query_norm.weight",
                        "attn.norm_added_k.weight": "txt_attn.norm.key_norm.weight",
                    }

        for k in block_map:
            key_map["{}.{}".format(prefix_from, k)] = "{}.{}".format(prefix_to, block_map[k])

    for index in range(n_single_layers):
        prefix_from = "single_transformer_blocks.{}".format(index)
        prefix_to = "{}single_blocks.{}".format(output_prefix, index)

        for end in ("weight", "bias"):
            k = "{}.attn.".format(prefix_from)
            qkv = "{}.linear1.{}".format(prefix_to, end)
            key_map["{}to_q.{}".format(k, end)] = (qkv, (0, 0, hidden_size))
            key_map["{}to_k.{}".format(k, end)] = (qkv, (0, hidden_size, hidden_size))
            key_map["{}to_v.{}".format(k, end)] = (qkv, (0, hidden_size * 2, hidden_size))
            key_map["{}.proj_mlp.{}".format(prefix_from, end)] = (qkv, (0, hidden_size * 3, hidden_size * 4))

        block_map = {
                        "norm.linear.weight": "modulation.lin.weight",
                        "norm.linear.bias": "modulation.lin.bias",
                        "proj_out.weight": "linear2.weight",
                        "proj_out.bias": "linear2.bias",
                        "attn.norm_q.weight": "norm.query_norm.weight",
                        "attn.norm_k.weight": "norm.key_norm.weight",
                        "attn.to_qkv_mlp_proj.weight": "linear1.weight", # Flux 2
                        "attn.to_out.weight": "linear2.weight", # Flux 2
                    }

        for k in block_map:
            key_map["{}.{}".format(prefix_from, k)] = "{}.{}".format(prefix_to, block_map[k])

    MAP_BASIC = {
        ("final_layer.linear.bias", "proj_out.bias"),
        ("final_layer.linear.weight", "proj_out.weight"),
        ("img_in.bias", "x_embedder.bias"),
        ("img_in.weight", "x_embedder.weight"),
        ("time_in.in_layer.bias", "time_text_embed.timestep_embedder.linear_1.bias"),
        ("time_in.in_layer.weight", "time_text_embed.timestep_embedder.linear_1.weight"),
        ("time_in.out_layer.bias", "time_text_embed.timestep_embedder.linear_2.bias"),
        ("time_in.out_layer.weight", "time_text_embed.timestep_embedder.linear_2.weight"),
        ("txt_in.bias", "context_embedder.bias"),
        ("txt_in.weight", "context_embedder.weight"),
        ("vector_in.in_layer.bias", "time_text_embed.text_embedder.linear_1.bias"),
        ("vector_in.in_layer.weight", "time_text_embed.text_embedder.linear_1.weight"),
        ("vector_in.out_layer.bias", "time_text_embed.text_embedder.linear_2.bias"),
        ("vector_in.out_layer.weight", "time_text_embed.text_embedder.linear_2.weight"),
        ("guidance_in.in_layer.bias", "time_text_embed.guidance_embedder.linear_1.bias"),
        ("guidance_in.in_layer.weight", "time_text_embed.guidance_embedder.linear_1.weight"),
        ("guidance_in.out_layer.bias", "time_text_embed.guidance_embedder.linear_2.bias"),
        ("guidance_in.out_layer.weight", "time_text_embed.guidance_embedder.linear_2.weight"),
        ("final_layer.adaLN_modulation.1.bias", "norm_out.linear.bias", swap_scale_shift),
        ("final_layer.adaLN_modulation.1.weight", "norm_out.linear.weight", swap_scale_shift),
        ("pos_embed_input.bias", "controlnet_x_embedder.bias"),
        ("pos_embed_input.weight", "controlnet_x_embedder.weight"),
    }

    for k in MAP_BASIC:
        if len(k) > 2:
            key_map[k[1]] = ("{}{}".format(output_prefix, k[0]), None, k[2])
        else:
            key_map[k[1]] = "{}{}".format(output_prefix, k[0])

    return key_map