async def test_bluetooth_discovery_with_cached_config(
    hass: HomeAssistant,
) -> None:
    """Test bluetooth discovery when validated config is already in cache."""
    # First, populate the cache via integration discovery
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
        data={
            "name": "Front Door",
            "address": YALE_ACCESS_LOCK_DISCOVERY_INFO.address,
            "key": "2fd51b8621c6a139eaffbedcb846b60f",
            "slot": 66,
            "serial": "M1XXX012LU",
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"

    # Now do bluetooth discovery with the cached config
    with patch(
        "homeassistant.components.yalexs_ble.PushLock.validate",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=YALE_ACCESS_LOCK_DISCOVERY_INFO,
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "integration_discovery_confirm"
    assert result["description_placeholders"] == {
        "name": "Front Door",
        "address": YALE_ACCESS_LOCK_DISCOVERY_INFO.address,
    }

    # Confirm the discovery
    with patch(
        "homeassistant.components.yalexs_ble.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Front Door"
    assert result["data"] == {
        CONF_LOCAL_NAME: YALE_ACCESS_LOCK_DISCOVERY_INFO.name,
        CONF_ADDRESS: YALE_ACCESS_LOCK_DISCOVERY_INFO.address,
        CONF_KEY: "2fd51b8621c6a139eaffbedcb846b60f",
        CONF_SLOT: 66,
    }