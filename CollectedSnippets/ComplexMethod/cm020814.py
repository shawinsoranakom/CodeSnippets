async def test_state_district(hass: HomeAssistant) -> None:
    """Test we can create entry for state + district."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result2["type"] is FlowResultType.FORM

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "region": "2",
        },
    )
    assert result3["type"] is FlowResultType.FORM

    with patch(
        "homeassistant.components.ukraine_alarm.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result4 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "region": "2.2",
            },
        )
        await hass.async_block_till_done()

    assert result4["type"] is FlowResultType.CREATE_ENTRY
    assert result4["title"] == "District 2.2"
    assert result4["data"] == {
        "region": "2.2",
        "name": result4["title"],
    }
    assert len(mock_setup_entry.mock_calls) == 1