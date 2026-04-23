def get_attn_backend_cls(
        cls,
        selected_backend: AttentionBackendEnum | None,
        attn_selector_config: AttentionSelectorConfig,
        num_heads: int | None = None,
    ) -> str:
        device_capability = cls.get_device_capability()
        assert device_capability is not None

        # First try checking just the selected backend, if there is one.
        if selected_backend is not None:
            try:
                backend_class = selected_backend.get_class()
                invalid_reasons = backend_class.validate_configuration(
                    device_capability=device_capability,
                    **attn_selector_config._asdict(),
                )
            except ImportError:
                invalid_reasons = ["ImportError"]
            if invalid_reasons:
                raise ValueError(
                    f"Selected backend {selected_backend} is not valid for "
                    f"this configuration. Reason: {invalid_reasons}"
                )
            else:
                logger.info("Using %s backend.", selected_backend)
                return selected_backend.get_path()

        # No selected backend or the selected backend is invalid,
        # so we try finding a valid backend.
        valid_backends_priorities, all_invalid_reasons = cls.get_valid_backends(
            device_capability=device_capability,
            attn_selector_config=attn_selector_config,
            num_heads=num_heads,
        )
        reasons_str = (
            "{"
            + ", ".join(
                f"{backend.name}: [{', '.join(reasons)}]"
                for backend, (_, reasons) in all_invalid_reasons.items()
            )
            + "}"
        )
        config_str = attn_selector_config.__repr__()
        logger.debug_once(
            f"Some attention backends are not valid for {cls.device_name} with "
            f"{config_str}. Reasons: {reasons_str}."
        )
        if len(valid_backends_priorities) == 0:
            raise ValueError(
                f"No valid attention backend found for {cls.device_name} "
                f"with {config_str}. Reasons: {reasons_str}."
            )

        # We have found some valid backends. Select the one with the
        # highest priority.
        sorted_indices = sorted(
            range(len(valid_backends_priorities)),
            key=lambda i: valid_backends_priorities[i][1],
        )
        selected_index = sorted_indices[0]
        selected_backend = valid_backends_priorities[selected_index][0]
        selected_priority = valid_backends_priorities[selected_index][1]

        # If the user specified --block-size (but not --attention-backend),
        # check whether that constraint precluded any higher-priority backends.
        if attn_selector_config.block_size is not None:
            excluded = [
                backend
                for backend, (priority, reasons) in all_invalid_reasons.items()
                if priority < selected_priority
                and reasons == ["block_size not supported"]
            ]
            if excluded:
                names = ", ".join(b.name for b in excluded)
                logger.warning(
                    "--block-size %d precluded higher-priority backend(s) "
                    "%s. Using %s instead, which may result in reduced "
                    "performance. Consider removing --block-size to "
                    "auto-select the optimal block size.",
                    attn_selector_config.block_size,
                    names,
                    selected_backend.name,
                )

        logger.info_once(
            "Using %s attention backend out of potential backends: %s.",
            selected_backend.name,
            "[" + ", ".join(f"'{b[0].name}'" for b in valid_backends_priorities) + "]",
        )

        return selected_backend.get_path()