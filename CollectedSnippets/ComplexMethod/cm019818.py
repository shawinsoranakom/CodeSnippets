async def test_user_step_auth_exception(hass: HomeAssistant) -> None:
    """Test user step with an authentication exception."""
    with patch(
        "homeassistant.components.yalexs_ble.config_flow.async_discovered_service_info",
        return_value=[YALE_ACCESS_LOCK_DISCOVERY_INFO, NOT_YALE_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ADDRESS: YALE_ACCESS_LOCK_DISCOVERY_INFO.address,
        },
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "key_slot"
    assert result2["errors"] == {}

    with patch(
        "homeassistant.components.yalexs_ble.config_flow.PushLock.validate",
        side_effect=AuthError,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_KEY: "2fd51b8621c6a139eaffbedcb846b60f",
                CONF_SLOT: 66,
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "key_slot"
    assert result3["errors"] == {CONF_KEY: "invalid_auth"}

    with (
        patch(
            "homeassistant.components.yalexs_ble.config_flow.PushLock.validate",
        ),
        patch(
            "homeassistant.components.yalexs_ble.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            {
                CONF_KEY: "2fd51b8621c6a139eaffbedcb846b60f",
                CONF_SLOT: 66,
            },
        )
        await hass.async_block_till_done()

    assert result4["type"] is FlowResultType.CREATE_ENTRY
    assert result4["title"] == f"{YALE_ACCESS_LOCK_DISCOVERY_INFO.name} (EEFF)"
    assert result4["data"] == {
        CONF_LOCAL_NAME: YALE_ACCESS_LOCK_DISCOVERY_INFO.name,
        CONF_ADDRESS: YALE_ACCESS_LOCK_DISCOVERY_INFO.address,
        CONF_KEY: "2fd51b8621c6a139eaffbedcb846b60f",
        CONF_SLOT: 66,
    }
    assert result4["result"].unique_id == YALE_ACCESS_LOCK_DISCOVERY_INFO.address
    assert len(mock_setup_entry.mock_calls) == 1