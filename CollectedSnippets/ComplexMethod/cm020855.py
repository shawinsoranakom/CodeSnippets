async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.trafikverket_ferry.config_flow.TrafikverketFerry.async_get_next_ferry_stop",
        ),
        patch(
            "homeassistant.components.trafikverket_ferry.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "1234567890",
                CONF_FROM: "Ekerö",
                CONF_TO: "Slagsta",
                CONF_TIME: "10:00",
                CONF_WEEKDAY: ["mon", "fri"],
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Ekerö to Slagsta at 10:00"
    assert result2["data"] == {
        "api_key": "1234567890",
        "name": "Ekerö to Slagsta at 10:00",
        "from": "Ekerö",
        "to": "Slagsta",
        "time": "10:00",
        "weekday": ["mon", "fri"],
    }
    assert len(mock_setup_entry.mock_calls) == 1
    assert result2["result"].unique_id == "eker\u00f6-slagsta-10:00-['mon', 'fri']"