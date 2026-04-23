async def test_form_coordinates(hass: HomeAssistant) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "location": config_flow.TYPE_SPECIFY_COORDINATES,
            "api_key": "api_key",
        },
    )
    assert result2["type"] is FlowResultType.FORM

    with patch(
        "homeassistant.components.co2signal.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                "latitude": 12.3,
                "longitude": 45.6,
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "12.3, 45.6"
    assert result3["data"] == {
        "latitude": 12.3,
        "longitude": 45.6,
        "api_key": "api_key",
    }
    assert len(mock_setup_entry.mock_calls) == 1