def _config_zero_init(config):
    configs_no_init = copy.deepcopy(config)
    for key in configs_no_init.__dict__:
        if (
            "init_range" in key
            or "initializer_range" in key
            or "_std" in key
            or "initializer_factor" in key
            or ("layer_scale" in key and key != "use_layer_scale")
        ):
            setattr(configs_no_init, key, 1e-10)
        if isinstance(getattr(configs_no_init, key, None), PreTrainedConfig):
            no_init_subconfig = _config_zero_init(getattr(configs_no_init, key))
            setattr(configs_no_init, key, no_init_subconfig)
    return configs_no_init