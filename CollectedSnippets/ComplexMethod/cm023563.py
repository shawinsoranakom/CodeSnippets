async def test_setup_entry(hass: HomeAssistant) -> None:
    """Test for successfully setting a config entry."""
    with (
        patch(
            "energyflip.EnergyFlip.authenticate", return_value=None
        ) as mock_authenticate,
        patch(
            "energyflip.EnergyFlip.is_authenticated", return_value=True
        ) as mock_is_authenticated,
        patch(
            "energyflip.EnergyFlip.current_measurements",
            return_value=MOCK_CURRENT_MEASUREMENTS,
        ) as mock_current_measurements,
    ):
        config_entry = MockConfigEntry(
            version=1,
            domain=DOMAIN,
            title="userId",
            data={
                CONF_ID: "userId",
                CONF_USERNAME: "username",
                CONF_PASSWORD: "password",
            },
            source="test",
        )
        config_entry.add_to_hass(hass)

        assert config_entry.state is ConfigEntryState.NOT_LOADED
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        # Assert integration is loaded
        assert config_entry.state is ConfigEntryState.LOADED

        # Assert entities are loaded
        entities = hass.states.async_entity_ids("sensor")
        assert len(entities) == 18

        # Assert mocks are called
        assert len(mock_authenticate.mock_calls) == 1
        assert len(mock_is_authenticated.mock_calls) == 1
        assert len(mock_current_measurements.mock_calls) == 1