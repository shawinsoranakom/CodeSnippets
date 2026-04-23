def convert_diffusers_mmdit(state_dict, output_prefix=""):
    out_sd = {}

    if 'joint_transformer_blocks.0.attn.add_k_proj.weight' in state_dict: #AuraFlow
        num_joint = count_blocks(state_dict, 'joint_transformer_blocks.{}.')
        num_single = count_blocks(state_dict, 'single_transformer_blocks.{}.')
        sd_map = comfy.utils.auraflow_to_diffusers({"n_double_layers": num_joint, "n_layers": num_joint + num_single}, output_prefix=output_prefix)
    elif 'adaln_single.emb.timestep_embedder.linear_1.bias' in state_dict and 'pos_embed.proj.bias' in state_dict: # PixArt
        num_blocks = count_blocks(state_dict, 'transformer_blocks.{}.')
        sd_map = comfy.utils.pixart_to_diffusers({"depth": num_blocks}, output_prefix=output_prefix)
    elif 'noise_refiner.0.attention.norm_k.weight' in state_dict:
        n_layers = count_blocks(state_dict, 'layers.{}.')
        dim = state_dict['noise_refiner.0.attention.to_k.weight'].shape[0]
        sd_map = comfy.utils.z_image_to_diffusers({"n_layers": n_layers, "dim": dim}, output_prefix=output_prefix)
        for k in state_dict: # For zeta chroma
            if k not in sd_map:
                sd_map[k] = k
    elif 'x_embedder.weight' in state_dict: #Flux
        depth = count_blocks(state_dict, 'transformer_blocks.{}.')
        depth_single_blocks = count_blocks(state_dict, 'single_transformer_blocks.{}.')
        hidden_size = state_dict["x_embedder.bias"].shape[0]
        sd_map = comfy.utils.flux_to_diffusers({"depth": depth, "depth_single_blocks": depth_single_blocks, "hidden_size": hidden_size}, output_prefix=output_prefix)
    elif 'transformer_blocks.0.attn.add_q_proj.weight' in state_dict and 'pos_embed.proj.weight' in state_dict: #SD3
        num_blocks = count_blocks(state_dict, 'transformer_blocks.{}.')
        depth = state_dict["pos_embed.proj.weight"].shape[0] // 64
        sd_map = comfy.utils.mmdit_to_diffusers({"depth": depth, "num_blocks": num_blocks}, output_prefix=output_prefix)
    else:
        return None

    for k in sd_map:
        weight = state_dict.get(k, None)
        if weight is not None:
            t = sd_map[k]

            if not isinstance(t, str):
                if len(t) > 2:
                    fun = t[2]
                else:
                    fun = lambda a: a
                offset = t[1]
                if offset is not None:
                    old_weight = out_sd.get(t[0], None)
                    if old_weight is None:
                        old_weight = torch.empty_like(weight)
                    if old_weight.shape[offset[0]] < offset[1] + offset[2]:
                        exp = list(weight.shape)
                        exp[offset[0]] = offset[1] + offset[2]
                        new = torch.empty(exp, device=weight.device, dtype=weight.dtype)
                        new[:old_weight.shape[0]] = old_weight
                        old_weight = new

                    if old_weight is out_sd.get(t[0], None) and comfy.memory_management.aimdo_enabled:
                        old_weight = old_weight.clone()

                    w = old_weight.narrow(offset[0], offset[1], offset[2])
                else:
                    if comfy.memory_management.aimdo_enabled:
                        weight = weight.clone()
                    old_weight = weight
                    w = weight
                w[:] = fun(weight)
                t = t[0]
                out_sd[t] = old_weight
            else:
                out_sd[t] = weight
            state_dict.pop(k)

    return out_sd