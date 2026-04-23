def _load_cached_autotuning(
    best_config: dict[str, JsonDataTy],
    configs_hash: str,
    configs: list[Config],
    inductor_meta: _InductorMetaTy,
) -> Config | None:
    if best_config is None:
        return None
    if best_config.pop("configs_hash", None) != configs_hash:
        return None

    # Remove time taken for comparison
    best_config.pop("time_taken_ms", None)

    best_config.pop("triton_cache_hash", None)

    # Extract extra_options if present. This allows third-party backends
    # to restore custom tuned options from the cache.
    extra_options = best_config.pop("extra_options", None)

    if inductor_meta.get("coordinate_descent_tuning") and best_config.pop(
        "found_by_coordesc", False
    ):
        num_warps = best_config.pop("num_warps")
        num_stages = best_config.pop("num_stages")

        # Extract common arguments
        config_args = {
            "num_warps": num_warps,
            "num_stages": num_stages,
        }

        if HAS_WARP_SPEC:
            config_args.update(
                {
                    "num_consumer_groups": best_config.pop("num_consumer_groups", 0),
                    "num_buffers_warp_spec": best_config.pop(
                        "num_buffers_warp_spec", 0
                    ),
                }
            )

        # Create the triton_config with the appropriate arguments
        # pyrefly: ignore [bad-argument-count, unexpected-keyword]
        triton_config = Config(best_config, **config_args)
        # pyrefly: ignore [missing-attribute]
        triton_config.found_by_coordesc = True
        # Restore extra_options (may be None if not used by backend)
        # pyrefly: ignore [missing-attribute]
        triton_config.extra_options = extra_options
        return triton_config

    matching_configs = [
        cfg
        for cfg in configs
        # pyrefly: ignore [missing-attribute]
        if all(val == best_config.get(key) for key, val in cfg.kwargs.items())
        # pyrefly: ignore [missing-attribute]
        and cfg.num_warps == best_config.get("num_warps")
        # pyrefly: ignore [missing-attribute]
        and cfg.num_stages == best_config.get("num_stages")
    ]
    if len(matching_configs) != 1:
        return None

    matched_config = matching_configs[0]
    # Restore extra_options (may be None if not used by backend)
    # pyrefly: ignore [missing-attribute]
    matched_config.extra_options = extra_options
    return matched_config