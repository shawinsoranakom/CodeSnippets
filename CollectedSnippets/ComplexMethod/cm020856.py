async def test_coordinator(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    monkeypatch: pytest.MonkeyPatch,
    get_ferries: list[FerryStopModel],
) -> None:
    """Test the Trafikverket Ferry coordinator."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data=ENTRY_CONFIG,
        entry_id="1",
        unique_id="123",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.trafikverket_ferry.coordinator.TrafikverketFerry.async_get_next_ferry_stops",
        return_value=get_ferries,
    ) as mock_data:
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        mock_data.assert_called_once()
        state1 = hass.states.get("sensor.harbor1_departure_from")
        state2 = hass.states.get("sensor.harbor1_departure_to")
        state3 = hass.states.get("sensor.harbor1_departure_time")
        assert state1.state == "Harbor 1"
        assert state2.state == "Harbor 2"
        assert state3.state == str(dt_util.now().year + 1) + "-05-01T12:00:00+00:00"
        mock_data.reset_mock()

        monkeypatch.setattr(
            get_ferries[0],
            "departure_time",
            datetime(dt_util.now().year + 2, 5, 1, 12, 0, tzinfo=dt_util.UTC),
        )

        freezer.tick(timedelta(minutes=6))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        mock_data.assert_called_once()
        state1 = hass.states.get("sensor.harbor1_departure_from")
        state2 = hass.states.get("sensor.harbor1_departure_to")
        state3 = hass.states.get("sensor.harbor1_departure_time")
        assert state1.state == "Harbor 1"
        assert state2.state == "Harbor 2"
        assert state3.state == str(dt_util.now().year + 2) + "-05-01T12:00:00+00:00"
        mock_data.reset_mock()

        mock_data.side_effect = NoFerryFound()
        freezer.tick(timedelta(minutes=6))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        mock_data.assert_called_once()
        state1 = hass.states.get("sensor.harbor1_departure_from")
        assert state1.state == STATE_UNAVAILABLE
        mock_data.reset_mock()

        mock_data.return_value = get_ferries
        mock_data.side_effect = None
        freezer.tick(timedelta(minutes=6))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        # mock_data.assert_called_once()
        state1 = hass.states.get("sensor.harbor1_departure_from")
        assert state1.state == "Harbor 1"
        mock_data.reset_mock()

        mock_data.side_effect = InvalidAuthentication()
        freezer.tick(timedelta(minutes=6))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        mock_data.assert_called_once()
        state1 = hass.states.get("sensor.harbor1_departure_from")
        assert state1.state == STATE_UNAVAILABLE
        mock_data.reset_mock()