def check_autotune_cache(
    configs: list[Config], filename: str | None, inductor_meta: dict[str, Any]
) -> tuple[list[Config], AutotuneCache | None, dict[str, Any]]:
    """
    Given a list of configs, checks autotune cache and return metadata
    """
    autotune_cache = None
    autotune_cache_info = {}
    disabled = inductor_meta.get("force_disable_caches", False)
    if (
        not disabled
        and filename is not None
        and (len(configs) > 1 or inductor_meta.get("coordinate_descent_tuning"))
        and os.environ.get("TRITON_INTERPRET", "0") != "1"
    ):
        configs_hash = hash_configs(configs)

        autotune_cache = AutotuneCache.create(inductor_meta, filename, configs_hash)
        if autotune_cache:
            if best_config := autotune_cache.read_best(inductor_meta, configs):
                configs = [best_config]
                autotune_cache_info["best_config"] = triton_config_to_hashable(
                    best_config
                )
                autotune_cache_info["autotune_cache_state"] = "hit"

            else:
                autotune_cache_info["autotune_cache_state"] = "miss"
                autotune_cache_info["num_configs"] = len(configs)
                if inductor_meta.get("coordinate_descent_tuning"):
                    autotune_cache_info["coordesc_tuning"] = True
                    if len(configs) == 1:
                        # This is the config that coordinate descent tuning started at, which
                        # is not the same as the final config chosen (i.e. only_config, best_config)
                        autotune_cache_info["coordesc_tuning_start_config"] = (
                            triton_config_to_hashable(configs[0])
                        )
    else:
        if len(configs) == 1:
            autotune_cache_info["autotune_cache_state"] = "only 1 config"
            autotune_cache_info["only_config"] = triton_config_to_hashable(configs[0])

        if disabled:
            autotune_cache_info["autotune_cache_state"] = "force_disabled"
            log.debug("autotune caching is disabled by config.force_disable_caches")

    return configs, autotune_cache, autotune_cache_info