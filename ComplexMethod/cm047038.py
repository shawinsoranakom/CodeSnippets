def prune_kernel_configs_backward_dX(configs: list[KernelConfigBackward_dX]):
    pruned_configs = []
    for config in configs:
        if config.use_tma_load_dy and config.permute_y:
            continue
        if config.permute_x and config.permute_y:
            continue
        if config.use_tma_store and config.permute_x:
            continue
        pruned_configs.append(config)
    return pruned_configs