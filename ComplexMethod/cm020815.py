async def test_state_district_community(hass: HomeAssistant) -> None:
    """Test we can create entry for state + district + community."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
    )
    assert result2["type"] is FlowResultType.FORM

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "region": "3",
        },
    )
    assert result3["type"] is FlowResultType.FORM

    result4 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "region": "3.2",
        },
    )
    assert result4["type"] is FlowResultType.FORM

    with patch(
        "homeassistant.components.ukraine_alarm.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result5 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "region": "3.2.1",
            },
        )
        await hass.async_block_till_done()

    assert result5["type"] is FlowResultType.CREATE_ENTRY
    assert result5["title"] == "Community 3.2.1"
    assert result5["data"] == {
        "region": "3.2.1",
        "name": result5["title"],
    }
    assert len(mock_setup_entry.mock_calls) == 1