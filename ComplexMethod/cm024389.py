async def test_options_flow(
    hass: HomeAssistant,
    get_trains: list[TrainStopModel],
    get_train_stop: TrainStopModel,
    get_train_stations: list[StationInfoModel],
) -> None:
    """Test a reauthentication flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "1234567890",
            CONF_NAME: "Stockholm C to Uppsala C at 10:00",
            CONF_FROM: "Cst",
            CONF_TO: "U",
            CONF_TIME: "10:00",
            CONF_WEEKDAY: WEEKDAYS,
        },
        version=2,
        minor_version=1,
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.trafikverket_train.coordinator.TrafikverketTrain.async_search_train_stations",
            side_effect=get_train_stations,
        ),
        patch(
            "homeassistant.components.trafikverket_train.coordinator.TrafikverketTrain.async_get_next_train_stops",
            return_value=get_trains,
        ),
        patch(
            "homeassistant.components.trafikverket_train.coordinator.TrafikverketTrain.async_get_train_station_from_signature",
        ),
        patch(
            "homeassistant.components.trafikverket_train.coordinator.TrafikverketTrain.async_get_train_stop",
            return_value=get_train_stop,
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(entry.entry_id)

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={"filter_product": "SJ Regionaltåg"},
        )
        await hass.async_block_till_done()

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"] == {"filter_product": "SJ Regionaltåg"}

        result = await hass.config_entries.options.async_init(entry.entry_id)

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={"filter_product": ""},
        )
        await hass.async_block_till_done()

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"] == {"filter_product": None}