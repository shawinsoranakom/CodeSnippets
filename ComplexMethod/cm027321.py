def device_info_from_specifications(
    specifications: dict[str, Any] | None,
) -> DeviceInfo | None:
    """Return a device description for device registry."""
    if not specifications:
        return None

    info = DeviceInfo(
        identifiers={(DOMAIN, id_) for id_ in specifications[CONF_IDENTIFIERS]},
        connections={
            (conn_[0], conn_[1]) for conn_ in specifications[CONF_CONNECTIONS]
        },
    )

    if CONF_MANUFACTURER in specifications:
        info[ATTR_MANUFACTURER] = specifications[CONF_MANUFACTURER]

    if CONF_MODEL in specifications:
        info[ATTR_MODEL] = specifications[CONF_MODEL]

    if CONF_MODEL_ID in specifications:
        info[ATTR_MODEL_ID] = specifications[CONF_MODEL_ID]

    if CONF_NAME in specifications:
        info[ATTR_NAME] = specifications[CONF_NAME]

    if CONF_HW_VERSION in specifications:
        info[ATTR_HW_VERSION] = specifications[CONF_HW_VERSION]

    if CONF_SERIAL_NUMBER in specifications:
        info[ATTR_SERIAL_NUMBER] = specifications[CONF_SERIAL_NUMBER]

    if CONF_SW_VERSION in specifications:
        info[ATTR_SW_VERSION] = specifications[CONF_SW_VERSION]

    if CONF_VIA_DEVICE in specifications:
        info[ATTR_VIA_DEVICE] = (DOMAIN, specifications[CONF_VIA_DEVICE])

    if CONF_SUGGESTED_AREA in specifications:
        info[ATTR_SUGGESTED_AREA] = specifications[CONF_SUGGESTED_AREA]

    if CONF_CONFIGURATION_URL in specifications:
        info[ATTR_CONFIGURATION_URL] = specifications[CONF_CONFIGURATION_URL]

    return info