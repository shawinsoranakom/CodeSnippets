async def test_async_step_user_linux_two_adapters(hass: HomeAssistant) -> None:
    """Test setting up manually with two adapters on Linux."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "multiple_adapters"
    assert result["data_schema"].schema["adapter"].container == {
        "hci0": "hci0 (00:00:00:00:00:01) ACME Bluetooth Adapter 5.0 (cc01:aa01)",
        "hci1": "hci1 (00:00:00:00:00:02) ACME Bluetooth Adapter 5.0 (cc01:aa01)",
    }
    with (
        patch("homeassistant.components.bluetooth.async_setup", return_value=True),
        patch(
            "homeassistant.components.bluetooth.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ADAPTER: "hci1"}
        )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "ACME Bluetooth Adapter 5.0 (00:00:00:00:00:02)"
    assert result2["data"] == {}
    assert len(mock_setup_entry.mock_calls) == 1