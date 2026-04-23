async def test_user_step_with_cached_config(hass: HomeAssistant) -> None:
    """Test user step when config is already cached from integration discovery."""
    # First, simulate integration discovery to populate the cache
    discovery_result = await hass.config_entries.flow.async_init(
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
    assert discovery_result["type"] is FlowResultType.ABORT
    assert discovery_result["reason"] == "no_devices_found"

    # Now start a user flow - it should use the cached config
    with patch(
        "homeassistant.components.yalexs_ble.config_flow.async_discovered_service_info",
        return_value=[YALE_ACCESS_LOCK_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # The dropdown should show "Front Door (AA:BB:CC:DD:EE:FF)" from cached config
    # This is the line 346 case we're testing
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ADDRESS: YALE_ACCESS_LOCK_DISCOVERY_INFO.address,
        },
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "key_slot"

    # The key_slot step should auto-complete with cached values
    # When no user input is provided, it should use the cached config
    with (
        patch(
            "homeassistant.components.yalexs_ble.config_flow.PushLock.validate",
        ),
        patch(
            "homeassistant.components.yalexs_ble.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        # No user input triggers using cached config
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            None,  # None triggers checking for cached config
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Front Door"  # Uses the name from cached config
    assert result3["data"] == {
        CONF_LOCAL_NAME: YALE_ACCESS_LOCK_DISCOVERY_INFO.name,
        CONF_ADDRESS: YALE_ACCESS_LOCK_DISCOVERY_INFO.address,
        CONF_KEY: "2fd51b8621c6a139eaffbedcb846b60f",
        CONF_SLOT: 66,
    }
    assert result3["result"].unique_id == YALE_ACCESS_LOCK_DISCOVERY_INFO.address
    assert len(mock_setup_entry.mock_calls) == 1