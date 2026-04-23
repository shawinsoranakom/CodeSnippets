async def test_form_options(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    user_input: dict[str, bool],
    expected: dict[str, bool],
) -> None:
    """Test the form options."""

    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2021-01-09 12:00:00+00:00")
    with patch(
        "homeassistant.components.aemet.AEMET.api_call",
        side_effect=mock_api_call,
    ):
        entry = MockConfigEntry(
            domain=DOMAIN, unique_id="40.30403754--3.72935236", data=CONFIG
        )
        entry.add_to_hass(hass)

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.LOADED

        result = await hass.config_entries.options.async_init(entry.entry_id)

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input=user_input
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert entry.options == {
            CONF_RADAR_UPDATES: expected[CONF_RADAR_UPDATES],
            CONF_STATION_UPDATES: expected[CONF_STATION_UPDATES],
        }

        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.LOADED