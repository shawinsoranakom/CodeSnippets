async def test_reauth(hass: HomeAssistant) -> None:
    """Test reauthentication."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_LOCAL_NAME: YALE_ACCESS_LOCK_DISCOVERY_INFO.name,
            CONF_ADDRESS: YALE_ACCESS_LOCK_DISCOVERY_INFO.address,
            CONF_KEY: "2fd51b8621c6a139eaffbedcb846b60f",
            CONF_SLOT: 66,
        },
        unique_id=YALE_ACCESS_LOCK_DISCOVERY_INFO.address,
    )
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_validate"

    with patch(
        "homeassistant.components.yalexs_ble.config_flow.PushLock.validate",
        side_effect=RuntimeError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_KEY: "2fd51b8621c6a139eaffbedcb846b60f",
                CONF_SLOT: 66,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "reauth_validate"
    assert result2["errors"] == {"base": "no_longer_in_range"}

    with (
        patch(
            "homeassistant.components.yalexs_ble.config_flow.async_ble_device_from_address",
            return_value=YALE_ACCESS_LOCK_DISCOVERY_INFO,
        ),
        patch(
            "homeassistant.components.yalexs_ble.config_flow.PushLock.validate",
        ),
        patch(
            "homeassistant.components.yalexs_ble.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_KEY: "2fd51b8621c6a139eaffbedcb846b60f",
                CONF_SLOT: 67,
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reauth_successful"
    assert len(mock_setup_entry.mock_calls) == 1