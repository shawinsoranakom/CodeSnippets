async def create_climate_entity(
    tado: TadoDataUpdateCoordinator, name: str, zone_id: int, device_info: dict
) -> TadoClimate | None:
    """Create a Tado climate entity."""
    capabilities = await tado.get_capabilities(zone_id)
    _LOGGER.debug("Capabilities for zone %s: %s", zone_id, capabilities)

    zone_type = capabilities["type"]
    support_flags = (
        ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    supported_hvac_modes = [
        TADO_TO_HA_HVAC_MODE_MAP[CONST_MODE_OFF],
        TADO_TO_HA_HVAC_MODE_MAP[CONST_MODE_SMART_SCHEDULE],
    ]
    supported_fan_modes: list[str] | None = None
    supported_swing_modes: list[str] | None = None
    heat_temperatures = None
    cool_temperatures = None

    if zone_type == TYPE_AIR_CONDITIONING:
        # Heat is preferred as it generally has a lower minimum temperature
        for mode in ORDERED_KNOWN_TADO_MODES:
            if mode not in capabilities:
                continue

            supported_hvac_modes.append(TADO_TO_HA_HVAC_MODE_MAP[mode])
            if (
                TADO_SWING_SETTING in capabilities[mode]
                or TADO_VERTICAL_SWING_SETTING in capabilities[mode]
                or TADO_VERTICAL_SWING_SETTING in capabilities[mode]
            ):
                support_flags |= ClimateEntityFeature.SWING_MODE
                supported_swing_modes = []
                if TADO_SWING_SETTING in capabilities[mode]:
                    supported_swing_modes.append(
                        TADO_TO_HA_SWING_MODE_MAP[TADO_SWING_ON]
                    )
                if TADO_VERTICAL_SWING_SETTING in capabilities[mode]:
                    supported_swing_modes.append(SWING_VERTICAL)
                if TADO_HORIZONTAL_SWING_SETTING in capabilities[mode]:
                    supported_swing_modes.append(SWING_HORIZONTAL)
                if (
                    SWING_HORIZONTAL in supported_swing_modes
                    and SWING_VERTICAL in supported_swing_modes
                ):
                    supported_swing_modes.append(SWING_BOTH)
                supported_swing_modes.append(TADO_TO_HA_SWING_MODE_MAP[TADO_SWING_OFF])

            if (
                TADO_FANSPEED_SETTING not in capabilities[mode]
                and TADO_FANLEVEL_SETTING not in capabilities[mode]
            ):
                continue

            support_flags |= ClimateEntityFeature.FAN_MODE

            if supported_fan_modes:
                continue

            if TADO_FANSPEED_SETTING in capabilities[mode]:
                supported_fan_modes = generate_supported_fanmodes(
                    TADO_TO_HA_FAN_MODE_MAP_LEGACY,
                    capabilities[mode][TADO_FANSPEED_SETTING],
                )

            else:
                supported_fan_modes = generate_supported_fanmodes(
                    TADO_TO_HA_FAN_MODE_MAP, capabilities[mode][TADO_FANLEVEL_SETTING]
                )

        cool_temperatures = capabilities[CONST_MODE_COOL]["temperatures"]
    else:
        supported_hvac_modes.append(HVACMode.HEAT)

    if CONST_MODE_HEAT in capabilities:
        heat_temperatures = capabilities[CONST_MODE_HEAT]["temperatures"]

    if heat_temperatures is None and "temperatures" in capabilities:
        heat_temperatures = capabilities["temperatures"]

    if cool_temperatures is None and heat_temperatures is None:
        _LOGGER.debug("Not adding zone %s since it has no temperatures", name)
        return None

    heat_min_temp = None
    heat_max_temp = None
    heat_step = None
    cool_min_temp = None
    cool_max_temp = None
    cool_step = None

    if heat_temperatures is not None:
        heat_min_temp = float(heat_temperatures["celsius"]["min"])
        heat_max_temp = float(heat_temperatures["celsius"]["max"])
        heat_step = heat_temperatures["celsius"].get("step", PRECISION_TENTHS)

    if cool_temperatures is not None:
        cool_min_temp = float(cool_temperatures["celsius"]["min"])
        cool_max_temp = float(cool_temperatures["celsius"]["max"])
        cool_step = cool_temperatures["celsius"].get("step", PRECISION_TENTHS)

    auto_geofencing_supported = await tado.get_auto_geofencing_supported()

    return TadoClimate(
        tado,
        name,
        zone_id,
        zone_type,
        supported_hvac_modes,
        support_flags,
        device_info,
        capabilities,
        auto_geofencing_supported,
        heat_min_temp,
        heat_max_temp,
        heat_step,
        cool_min_temp,
        cool_max_temp,
        cool_step,
        supported_fan_modes,
        supported_swing_modes,
    )