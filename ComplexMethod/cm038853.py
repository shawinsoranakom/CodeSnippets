def autotune_kernel(
    kernel_name: str,
    platform: str,
    config_manager: ConfigManager,
    force: bool = False,
    autotune_effort: str = "quick",
) -> AutotuneResult:
    logger.debug(
        "Starting autotune for kernel '%s' with effort='%s'",
        kernel_name,
        autotune_effort,
    )
    kernel_wrapper = get_kernel_by_name(kernel_name)
    if kernel_wrapper is None:
        error_msg = f"Kernel '{kernel_name}' not found in registry"
        logger.error(error_msg)
        return AutotuneResult(
            status="error",
            message=error_msg,
            successful=0,
            failed=0,
            configs={},
        )

    try:
        with FakeTensorMode():
            all_config_keys = list(kernel_wrapper.get_inputs().keys())
    except NotImplementedError:
        error_msg = f"Kernel '{kernel_name}' has no input generator registered"
        logger.error(error_msg)
        return AutotuneResult(
            status="error",
            message=error_msg,
            successful=0,
            failed=0,
            configs={},
        )

    try:
        logger.info(
            "Autotuning kernel '%s' for platform '%s' with %d configs",
            kernel_name,
            platform,
            len(all_config_keys),
        )

        if not force:
            existing_configs = config_manager.get_platform_configs(
                kernel_name, platform
            )
            keys_to_autotune = []
            for config_key in all_config_keys:
                if config_key in existing_configs:
                    logger.debug(
                        "Config '%s' already exists for platform '%s', skipping",
                        config_key,
                        platform,
                    )
                else:
                    keys_to_autotune.append(config_key)
        else:
            logger.debug("Force mode enabled, will re-autotune all configs")
            keys_to_autotune = all_config_keys

        if not keys_to_autotune:
            logger.info(
                "All configs already exist for kernel '%s' on platform '%s'. "
                "Use --force to re-autotune.",
                kernel_name,
                platform,
            )
            return AutotuneResult(
                status="skipped",
                message="All configs already exist",
                successful=0,
                failed=0,
                configs={},
            )

        inputs_dict = kernel_wrapper.get_inputs()
        configs_to_autotune = {k: inputs_dict[k] for k in keys_to_autotune}

        total_start_time = time.time()
        autotuned_configs = {}
        failed_configs = []

        for config_key, inputs in configs_to_autotune.items():
            logger.info("Autotuning config: %s", config_key)
            logger.debug(
                "Input shapes: %s",
                [getattr(inp, "shape", type(inp).__name__) for inp in inputs],
            )

            try:
                config_start_time = time.time()
                config = kernel_wrapper.run_autotune(inputs, autotune_effort)
                config_duration = time.time() - config_start_time

                # Save immediately for checkpointing
                config_manager.save_configs(kernel_name, platform, {config_key: config})

                autotuned_configs[config_key] = config
                logger.debug("Config details: %s", config)

                logger.info(
                    "✓ Autotuned and saved config '%s' (%.2fs)",
                    config_key,
                    config_duration,
                )

            except (RuntimeError, ValueError, OSError) as e:
                logger.exception(
                    "Failed to autotune config '%s': %s",
                    config_key,
                    e,
                )
                failed_configs.append(config_key)

        total_duration = time.time() - total_start_time
        successful = len(autotuned_configs)
        failed = len(failed_configs)

        logger.info(
            "Completed autotuning for kernel '%s': %d successful, %d failed (%.2fs)",
            kernel_name,
            successful,
            failed,
            total_duration,
        )

        status = "success" if failed == 0 else "partial"
        return AutotuneResult(
            status=status,
            successful=successful,
            failed=failed,
            configs=autotuned_configs,
        )

    except (KeyError, RuntimeError, ValueError, OSError) as e:
        error_msg = f"Unexpected error: {e}"
        logger.exception("Failed to autotune kernel '%s': %s", kernel_name, e)
        return AutotuneResult(
            status="error",
            message=error_msg,
            successful=0,
            failed=0,
            configs={},
        )