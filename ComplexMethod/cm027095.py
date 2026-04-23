def warn_if_topic_duplicated(
    hass: HomeAssistant,
    command_topic: str,
    own_mac: str | None,
    own_device_config: TasmotaDeviceConfig,
) -> bool:
    """Log and create repairs issue if several devices share the same topic."""
    duplicated = False
    offenders = []
    for other_mac, other_config in hass.data[DISCOVERY_DATA].items():
        if own_mac and other_mac == own_mac:
            continue
        if command_topic == get_topic_command(other_config):
            offenders.append((other_mac, tasmota_get_device_config(other_config)))
    issue_id = f"topic_duplicated_{command_topic}"
    if offenders:
        if own_mac:
            offenders.append((own_mac, own_device_config))
        offender_strings = [
            f"'{cfg[tasmota_const.CONF_NAME]}' ({cfg[tasmota_const.CONF_IP]})"
            for _, cfg in offenders
        ]
        _LOGGER.warning(
            (
                "Multiple Tasmota devices are sharing the same topic '%s'. Offending"
                " devices: %s"
            ),
            command_topic,
            ", ".join(offender_strings),
        )
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            data={
                "key": "topic_duplicated",
                "mac": " ".join([mac for mac, _ in offenders]),
                "topic": command_topic,
            },
            is_fixable=False,
            learn_more_url=MQTT_TOPIC_URL,
            severity=ir.IssueSeverity.ERROR,
            translation_key="topic_duplicated",
            translation_placeholders={
                "topic": command_topic,
                "offenders": "\n\n* " + "\n\n* ".join(offender_strings),
            },
        )
        duplicated = True
    return duplicated