def load_network(name, network_on_disk):
    net = network.Network(name, network_on_disk)
    net.mtime = os.path.getmtime(network_on_disk.filename)

    sd = sd_models.read_state_dict(network_on_disk.filename)

    # this should not be needed but is here as an emergency fix for an unknown error people are experiencing in 1.2.0
    if not hasattr(shared.sd_model, 'network_layer_mapping'):
        assign_network_names_to_compvis_modules(shared.sd_model)

    keys_failed_to_match = {}
    is_sd2 = 'model_transformer_resblocks' in shared.sd_model.network_layer_mapping
    if hasattr(shared.sd_model, 'diffusers_weight_map'):
        diffusers_weight_map = shared.sd_model.diffusers_weight_map
    elif hasattr(shared.sd_model, 'diffusers_weight_mapping'):
        diffusers_weight_map = {}
        for k, v in shared.sd_model.diffusers_weight_mapping():
            diffusers_weight_map[k] = v
        shared.sd_model.diffusers_weight_map = diffusers_weight_map
    else:
        diffusers_weight_map = None

    matched_networks = {}
    bundle_embeddings = {}

    for key_network, weight in sd.items():

        if diffusers_weight_map:
            key_network_without_network_parts, network_name, network_weight = key_network.rsplit(".", 2)
            network_part = network_name + '.' + network_weight
        else:
            key_network_without_network_parts, _, network_part = key_network.partition(".")

        if key_network_without_network_parts == "bundle_emb":
            emb_name, vec_name = network_part.split(".", 1)
            emb_dict = bundle_embeddings.get(emb_name, {})
            if vec_name.split('.')[0] == 'string_to_param':
                _, k2 = vec_name.split('.', 1)
                emb_dict['string_to_param'] = {k2: weight}
            else:
                emb_dict[vec_name] = weight
            bundle_embeddings[emb_name] = emb_dict

        if diffusers_weight_map:
            key = diffusers_weight_map.get(key_network_without_network_parts, key_network_without_network_parts)
        else:
            key = convert_diffusers_name_to_compvis(key_network_without_network_parts, is_sd2)

        sd_module = shared.sd_model.network_layer_mapping.get(key, None)

        if sd_module is None:
            m = re_x_proj.match(key)
            if m:
                sd_module = shared.sd_model.network_layer_mapping.get(m.group(1), None)

        # SDXL loras seem to already have correct compvis keys, so only need to replace "lora_unet" with "diffusion_model"
        if sd_module is None and "lora_unet" in key_network_without_network_parts:
            key = key_network_without_network_parts.replace("lora_unet", "diffusion_model")
            sd_module = shared.sd_model.network_layer_mapping.get(key, None)
        elif sd_module is None and "lora_te1_text_model" in key_network_without_network_parts:
            key = key_network_without_network_parts.replace("lora_te1_text_model", "0_transformer_text_model")
            sd_module = shared.sd_model.network_layer_mapping.get(key, None)

            # some SD1 Loras also have correct compvis keys
            if sd_module is None:
                key = key_network_without_network_parts.replace("lora_te1_text_model", "transformer_text_model")
                sd_module = shared.sd_model.network_layer_mapping.get(key, None)

        # kohya_ss OFT module
        elif sd_module is None and "oft_unet" in key_network_without_network_parts:
            key = key_network_without_network_parts.replace("oft_unet", "diffusion_model")
            sd_module = shared.sd_model.network_layer_mapping.get(key, None)

        # KohakuBlueLeaf OFT module
        if sd_module is None and "oft_diag" in key:
            key = key_network_without_network_parts.replace("lora_unet", "diffusion_model")
            key = key_network_without_network_parts.replace("lora_te1_text_model", "0_transformer_text_model")
            sd_module = shared.sd_model.network_layer_mapping.get(key, None)

        if sd_module is None:
            keys_failed_to_match[key_network] = key
            continue

        if key not in matched_networks:
            matched_networks[key] = network.NetworkWeights(network_key=key_network, sd_key=key, w={}, sd_module=sd_module)

        matched_networks[key].w[network_part] = weight

    for key, weights in matched_networks.items():
        net_module = None
        for nettype in module_types:
            net_module = nettype.create_module(net, weights)
            if net_module is not None:
                break

        if net_module is None:
            raise AssertionError(f"Could not find a module type (out of {', '.join([x.__class__.__name__ for x in module_types])}) that would accept those keys: {', '.join(weights.w)}")

        net.modules[key] = net_module

    embeddings = {}
    for emb_name, data in bundle_embeddings.items():
        embedding = textual_inversion.create_embedding_from_data(data, emb_name, filename=network_on_disk.filename + "/" + emb_name)
        embedding.loaded = None
        embedding.shorthash = BundledTIHash(name)
        embeddings[emb_name] = embedding

    net.bundle_embeddings = embeddings

    if keys_failed_to_match:
        logging.debug(f"Network {network_on_disk.filename} didn't match keys: {keys_failed_to_match}")

    return net