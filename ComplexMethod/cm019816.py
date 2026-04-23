async def test_user_step_invalid_keys(hass: HomeAssistant) -> None:
    """Test user step with invalid keys tried first."""
    with patch(
        "homeassistant.components.yalexs_ble.config_flow.async_discovered_service_info",
        return_value=[YALE_ACCESS_LOCK_DISCOVERY_INFO],
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

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {
            CONF_KEY: "dog",
            CONF_SLOT: 66,
        },
    )
    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "key_slot"
    assert result3["errors"] == {CONF_KEY: "invalid_key_format"}

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        {
            CONF_KEY: "qfd51b8621c6a139eaffbedcb846b60f",
            CONF_SLOT: 66,
        },
    )
    assert result4["type"] is FlowResultType.FORM
    assert result4["step_id"] == "key_slot"
    assert result4["errors"] == {CONF_KEY: "invalid_key_format"}

    result5 = await hass.config_entries.flow.async_configure(
        result4["flow_id"],
        {
            CONF_KEY: "2fd51b8621c6a139eaffbedcb846b60f",
            CONF_SLOT: 999,
        },
    )
    assert result5["type"] is FlowResultType.FORM
    assert result5["step_id"] == "key_slot"
    assert result5["errors"] == {CONF_SLOT: "invalid_key_index"}

    with (
        patch(
            "homeassistant.components.yalexs_ble.config_flow.PushLock.validate",
        ),
        patch(
            "homeassistant.components.yalexs_ble.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result6 = await hass.config_entries.flow.async_configure(
            result5["flow_id"],
            {
                CONF_KEY: "2fd51b8621c6a139eaffbedcb846b60f",
                CONF_SLOT: 66,
            },
        )
        await hass.async_block_till_done()

    assert result6["type"] is FlowResultType.CREATE_ENTRY
    assert result6["title"] == f"{YALE_ACCESS_LOCK_DISCOVERY_INFO.name} (EEFF)"
    assert result6["data"] == {
        CONF_LOCAL_NAME: YALE_ACCESS_LOCK_DISCOVERY_INFO.name,
        CONF_ADDRESS: YALE_ACCESS_LOCK_DISCOVERY_INFO.address,
        CONF_KEY: "2fd51b8621c6a139eaffbedcb846b60f",
        CONF_SLOT: 66,
    }
    assert result6["result"].unique_id == YALE_ACCESS_LOCK_DISCOVERY_INFO.address
    assert len(mock_setup_entry.mock_calls) == 1