async def test_bluetooth_step_success(hass: HomeAssistant) -> None:
    """Test bluetooth step success path."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=YALE_ACCESS_LOCK_DISCOVERY_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "key_slot"
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.yalexs_ble.config_flow.PushLock.validate",
        ),
        patch(
            "homeassistant.components.yalexs_ble.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_KEY: "2fd51b8621c6a139eaffbedcb846b60f",
                CONF_SLOT: 66,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == f"{YALE_ACCESS_LOCK_DISCOVERY_INFO.name} (EEFF)"
    assert result2["data"] == {
        CONF_LOCAL_NAME: YALE_ACCESS_LOCK_DISCOVERY_INFO.name,
        CONF_ADDRESS: YALE_ACCESS_LOCK_DISCOVERY_INFO.address,
        CONF_KEY: "2fd51b8621c6a139eaffbedcb846b60f",
        CONF_SLOT: 66,
    }
    assert result2["result"].unique_id == YALE_ACCESS_LOCK_DISCOVERY_INFO.address
    assert len(mock_setup_entry.mock_calls) == 1