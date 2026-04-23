def remove_feature_flags(
    kernel_configs: list[KernelConfig],
    permute_x: bool = True,
    permute_y: bool = True,
    tma_loads: bool = True,
    tma_store: bool = True,
):
    pruned_configs = []
    for config in kernel_configs:
        # Remove permute flags first:
        if permute_x and config.permute_x:
            continue
        if permute_y and config.permute_y:
            continue
        if tma_loads:
            if isinstance(config, KernelConfigForward):
                if config.use_tma_load_w or config.use_tma_load_x:
                    continue
            if isinstance(config, KernelConfigBackward_dX):
                if config.use_tma_load_dy or config.use_tma_load_w:
                    continue
            if isinstance(config, KernelConfigBackward_dW):
                if config.use_tma_load_dy or config.use_tma_load_x:
                    continue
        if tma_store:
            if config.use_tma_store:
                continue
        pruned_configs.append(config)
    return pruned_configs