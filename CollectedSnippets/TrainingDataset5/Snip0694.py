def assign_network_names_to_compvis_modules(sd_model):
    network_layer_mapping = {}

    if shared.sd_model.is_sdxl:
        for i, embedder in enumerate(shared.sd_model.conditioner.embedders):
            if not hasattr(embedder, 'wrapped'):
                continue

            for name, module in embedder.wrapped.named_modules():
                network_name = f'{i}_{name.replace(".", "_")}'
                network_layer_mapping[network_name] = module
                module.network_layer_name = network_name
    else:
        cond_stage_model = getattr(shared.sd_model.cond_stage_model, 'wrapped', shared.sd_model.cond_stage_model)

        for name, module in cond_stage_model.named_modules():
            network_name = name.replace(".", "_")
            network_layer_mapping[network_name] = module
            module.network_layer_name = network_name

    for name, module in shared.sd_model.model.named_modules():
        network_name = name.replace(".", "_")
        network_layer_mapping[network_name] = module
        module.network_layer_name = network_name

    sd_model.network_layer_mapping = network_layer_mapping
