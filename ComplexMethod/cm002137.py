def get_config_by_level(level: int) -> list[BenchmarkConfig]:
    configs = []
    # Early return if level is greater than 3: we generate all combinations of configs, maybe even w/ all compile modes
    if level >= 3:
        for attn_implementation in BenchmarkConfig.all_attn_implementations:
            # Usually there is not much to gain by compiling with other modes, but we allow it for level 4
            compile_modes = BenchmarkConfig.all_compiled_modes if level >= 4 else [None, "default"]
            for cm in compile_modes:
                compile_kwargs = {"mode": cm} if cm is not None else None
                for kernelize_on in {False, KERNELIZATION_AVAILABLE}:
                    for cb_on in [False, True]:
                        configs.append(
                            BenchmarkConfig(
                                attn_implementation=attn_implementation,
                                compile_kwargs=compile_kwargs,
                                kernelize=kernelize_on,
                                continuous_batching=cb_on,
                            )
                        )
        return configs
    # Otherwise, we add the configs for the given level
    if level >= 0:
        configs.append(BenchmarkConfig(attn_implementation="flex_attention", compile_kwargs={}))
    if level >= 1:
        configs.append(BenchmarkConfig(attn_implementation="flash_attention_2"))
        configs.append(BenchmarkConfig(attn_implementation="eager", compile_kwargs={}))
        configs.append(BenchmarkConfig(attn_implementation="flash_attention_2", continuous_batching=True))
    if level >= 2:
        configs.append(BenchmarkConfig(attn_implementation="sdpa", compile_kwargs={}))
        configs.append(BenchmarkConfig(attn_implementation="flex_attention", compile_kwargs={}, kernelize=True))
        configs.append(BenchmarkConfig(attn_implementation="flash_attention_2", kernelize=True))
        configs.append(BenchmarkConfig(attn_implementation="sdpa", continuous_batching=True))
    return configs