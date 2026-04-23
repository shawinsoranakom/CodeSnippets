async def test_ssdp(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    radio_id_return_value: str | None,
    radio_id_side_effect: Exception | None,
) -> None:
    """Test a device being discovered."""
    with patch(
        "homeassistant.components.frontier_silicon.config_flow.AFSAPI.get_radio_id",
        return_value=radio_id_return_value,
        side_effect=radio_id_side_effect,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=MOCK_DISCOVERY,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    flow = flows[0]
    assert flow["context"]["title_placeholders"] == {"name": "Speaker Name"}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Name of the device"
    assert result2["data"] == {
        CONF_WEBFSAPI_URL: "http://1.1.1.1:80/webfsapi",
        CONF_PIN: DEFAULT_PIN,
    }
    mock_setup_entry.assert_called_once()