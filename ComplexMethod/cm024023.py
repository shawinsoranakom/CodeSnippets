async def test_async_step_integration_discovery(hass: HomeAssistant) -> None:
    """Test setting up from integration discovery."""

    details = AdapterDetails(
        address="00:00:00:00:00:01",
        sw_version="1.23.5",
        hw_version="1.2.3",
        manufacturer="ACME",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
        data={CONF_ADAPTER: "hci0", CONF_DETAILS: details},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["description_placeholders"] == {
        "name": "hci0 (00:00:00:00:00:01)",
        "model": "Unknown",
        "manufacturer": "ACME",
    }
    assert result["step_id"] == "single_adapter"
    with (
        patch("homeassistant.components.bluetooth.async_setup", return_value=True),
        patch(
            "homeassistant.components.bluetooth.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "ACME Unknown (00:00:00:00:00:01)"
    assert result2["data"] == {}
    assert len(mock_setup_entry.mock_calls) == 1