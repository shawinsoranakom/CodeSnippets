async def async_setup_entry(hass: HomeAssistant, entry: ElkM1ConfigEntry) -> bool:
    """Set up Elk-M1 Control from a config entry."""
    conf = entry.data

    host = hostname_from_url(entry.data[CONF_HOST])

    _LOGGER.debug("Setting up elkm1 %s", conf["host"])

    if (not entry.unique_id or ":" not in entry.unique_id) and is_ip_address(host):
        _LOGGER.debug(
            "Unique id for %s is missing during setup, trying to fill from discovery",
            host,
        )
        if device := await async_discover_device(hass, host):
            async_update_entry_from_discovery(hass, entry, device)

    config: dict[str, Any] = {}

    if not conf[CONF_AUTO_CONFIGURE]:
        # With elkm1-lib==0.7.16 and later auto configure is available
        config["panel"] = {"enabled": True, "included": [True]}
        for item, max_ in ELK_ELEMENTS.items():
            config[item] = {
                "enabled": conf[item][CONF_ENABLED],
                "included": [not conf[item]["include"]] * max_,
            }
            try:
                _included(conf[item]["include"], True, config[item]["included"])
                _included(conf[item]["exclude"], False, config[item]["included"])
            except (ValueError, vol.Invalid) as err:
                _LOGGER.error("Config item: %s; %s", item, err)
                return False

    elk = Elk(
        {
            "url": conf[CONF_HOST],
            "userid": conf[CONF_USERNAME],
            "password": conf[CONF_PASSWORD],
        }
    )
    elk.connect()

    def _keypad_changed(keypad: Element, changeset: dict[str, Any]) -> None:
        if (keypress := changeset.get("last_keypress")) is None:
            return

        hass.bus.async_fire(
            EVENT_ELKM1_KEYPAD_KEY_PRESSED,
            {
                ATTR_KEYPAD_NAME: keypad.name,
                ATTR_KEYPAD_ID: keypad.index + 1,
                ATTR_KEY_NAME: keypress[0],
                ATTR_KEY: keypress[1],
            },
        )

    for keypad in elk.keypads:
        keypad.add_callback(_keypad_changed)

    sync_success = False
    try:
        await ElkSyncWaiter(elk, LOGIN_TIMEOUT, SYNC_TIMEOUT).async_wait()
        sync_success = True
    except LoginFailed:
        _LOGGER.error("ElkM1 login failed for %s", conf[CONF_HOST])
        return False
    except TimeoutError as exc:
        raise ConfigEntryNotReady(f"Timed out connecting to {conf[CONF_HOST]}") from exc
    finally:
        if not sync_success:
            elk.disconnect()

    elk_temp_unit = elk.panel.temperature_units
    if elk_temp_unit == "C":
        temperature_unit = UnitOfTemperature.CELSIUS  # type: ignore[unreachable]
    else:
        temperature_unit = UnitOfTemperature.FAHRENHEIT
    config["temperature_unit"] = temperature_unit
    prefix: str = conf[CONF_PREFIX]
    auto_configure: bool = conf[CONF_AUTO_CONFIGURE]
    entry.runtime_data = ELKM1Data(
        elk=elk,
        prefix=prefix,
        mac=entry.unique_id,
        auto_configure=auto_configure,
        config=config,
        keypads={},
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True