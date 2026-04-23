async def _service_handler(call: ServiceCall) -> None:
    """Apply a service."""
    host = call.data.get(ATTR_HOST)

    entry: NetgearLTEConfigEntry | None = None
    for entry in call.hass.config_entries.async_loaded_entries(DOMAIN):
        if entry.data.get(CONF_HOST) == host:
            break

    if not entry or not (modem := entry.runtime_data.modem).token:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="config_entry_not_found",
            translation_placeholders={"service": call.service},
        )

    if call.service == SERVICE_DELETE_SMS:
        for sms_id in call.data[ATTR_SMS_ID]:
            await modem.delete_sms(sms_id)
    elif call.service == SERVICE_SET_OPTION:
        if failover := call.data.get(ATTR_FAILOVER):
            await modem.set_failover_mode(failover)
        if autoconnect := call.data.get(ATTR_AUTOCONNECT):
            await modem.set_autoconnect_mode(autoconnect)
    elif call.service == SERVICE_CONNECT_LTE:
        await modem.connect_lte()
    elif call.service == SERVICE_DISCONNECT_LTE:
        await modem.disconnect_lte()