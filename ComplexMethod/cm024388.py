async def test_form(
    hass: HomeAssistant, get_train_stations: list[StationInfoModel]
) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "initial"
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.trafikverket_train.coordinator.TrafikverketTrain.async_search_train_stations",
            side_effect=get_train_stations,
        ),
        patch(
            "homeassistant.components.trafikverket_train.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "1234567890",
                CONF_FROM: "Stockholm C",
                CONF_TO: "Uppsala C",
                CONF_TIME: "10:00",
                CONF_WEEKDAY: ["mon", "fri"],
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Stockholm C to Uppsala C at 10:00"
    assert result["data"] == {
        "api_key": "1234567890",
        "name": "Stockholm C to Uppsala C at 10:00",
        "from": "Cst",
        "to": "U",
        "time": "10:00",
        "weekday": ["mon", "fri"],
    }
    assert result["options"] == {"filter_product": None}
    assert len(mock_setup_entry.mock_calls) == 1