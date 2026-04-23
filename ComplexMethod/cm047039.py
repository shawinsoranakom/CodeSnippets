def prune_kernel_configs_backward_dW(configs: list[KernelConfigBackward_dW]):
    pruned_configs = []
    for config in configs:
        if config.use_tma_load_dy and config.permute_y:
            continue
        if config.use_tma_load_x and config.permute_x:
            continue
        if config.permute_x and config.permute_y:
            continue
        pruned_configs.append(config)
    return pruned_configs