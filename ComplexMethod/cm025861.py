def _validate_set_system_mode_params(tcs: ControlSystem, data: dict[str, Any]) -> None:
    """Validate that a set_system_mode service call is properly formed."""

    mode = data[ATTR_MODE]
    tcs_modes = {m[SZ_SYSTEM_MODE]: m for m in tcs.allowed_system_modes}

    # Validation occurs here, instead of in the library, because it uses a slightly
    # different schema (until instead of duration/period) for the method invoked
    # via this service call

    if (mode_info := tcs_modes.get(mode)) is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="mode_not_supported",
            translation_placeholders={ATTR_MODE: mode},
        )

    # voluptuous schema ensures that duration and period are not both present

    if not mode_info[SZ_CAN_BE_TEMPORARY]:
        if ATTR_DURATION in data or ATTR_PERIOD in data:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="mode_cant_be_temporary",
                translation_placeholders={ATTR_MODE: mode},
            )
        return

    timing_mode = mode_info.get(SZ_TIMING_MODE)  # will not be None, as can_be_temporary

    if timing_mode == SZ_DURATION and ATTR_PERIOD in data:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="mode_cant_have_period",
            translation_placeholders={ATTR_MODE: mode},
        )

    if timing_mode == SZ_PERIOD and ATTR_DURATION in data:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="mode_cant_have_duration",
            translation_placeholders={ATTR_MODE: mode},
        )