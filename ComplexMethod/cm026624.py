def _get_placeholders(hass: HomeAssistant, issue_type: str) -> dict[str, str] | None:
    currency = hass.config.currency
    if issue_type == ENERGY_UNIT_ERROR:
        return {
            "energy_units": ", ".join(
                ENERGY_USAGE_UNITS[sensor.SensorDeviceClass.ENERGY]
            ),
        }
    if issue_type == ENERGY_PRICE_UNIT_ERROR:
        return {
            "price_units": ", ".join(
                f"{currency}{unit}" for unit in ENERGY_PRICE_UNITS
            ),
        }
    if issue_type == POWER_UNIT_ERROR:
        return {
            "power_units": ", ".join(POWER_USAGE_UNITS[sensor.SensorDeviceClass.POWER]),
        }
    if issue_type == GAS_UNIT_ERROR:
        return {
            "energy_units": ", ".join(GAS_USAGE_UNITS[sensor.SensorDeviceClass.ENERGY]),
            "gas_units": ", ".join(GAS_USAGE_UNITS[sensor.SensorDeviceClass.GAS]),
        }
    if issue_type == GAS_PRICE_UNIT_ERROR:
        return {
            "price_units": ", ".join(f"{currency}{unit}" for unit in GAS_PRICE_UNITS),
        }
    if issue_type == WATER_UNIT_ERROR:
        return {
            "water_units": ", ".join(WATER_USAGE_UNITS[sensor.SensorDeviceClass.WATER]),
        }
    if issue_type == WATER_PRICE_UNIT_ERROR:
        return {
            "price_units": ", ".join(f"{currency}{unit}" for unit in WATER_PRICE_UNITS),
        }
    if issue_type == VOLUME_FLOW_RATE_UNIT_ERROR:
        return {
            "flow_rate_units": ", ".join(
                VOLUME_FLOW_RATE_UNITS[sensor.SensorDeviceClass.VOLUME_FLOW_RATE]
            ),
        }
    return None