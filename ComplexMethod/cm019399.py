async def test_adam_restore_state_climate(
    hass: HomeAssistant,
    mock_smile_adam_heat_cool: MagicMock,
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test restore_state for climate with restored schedule."""
    mock_restore_cache_with_extra_data(
        hass,
        [
            (
                State("climate.living_room", "heat"),
                PlugwiseClimateExtraStoredData(
                    last_active_schedule=None,
                    previous_action_mode="heating",
                ).as_dict(),
            ),
            (
                State("climate.bathroom", "heat"),
                PlugwiseClimateExtraStoredData(
                    last_active_schedule="Badkamer",
                    previous_action_mode="heating",
                ).as_dict(),
            ),
        ],
    )

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert (state := hass.states.get("climate.living_room"))
    assert state.state == "heat"

    # Verify a HomeAssistantError is raised setting a schedule with last_active_schedule = None
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.living_room", ATTR_HVAC_MODE: HVACMode.AUTO},
            blocking=True,
        )

    data = mock_smile_adam_heat_cool.async_update.return_value
    data["f2bf9048bef64cc5b6d5110154e33c81"]["climate_mode"] = "off"
    data["da224107914542988a88561b4452b0f6"]["selec_regulation_mode"] = "off"
    with patch(HA_PLUGWISE_SMILE_ASYNC_UPDATE, return_value=data):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

        assert (state := hass.states.get("climate.living_room"))
        assert state.state == "off"

        # Verify restoration of previous_action_mode = heating
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.living_room", ATTR_HVAC_MODE: HVACMode.HEAT},
            blocking=True,
        )
        mock_smile_adam_heat_cool.set_regulation_mode.assert_called_with(
            "heating",
        )
        assert mock_smile_adam_heat_cool.set_regulation_mode.call_count == 1

    data = mock_smile_adam_heat_cool.async_update.return_value
    data["f871b8c4d63549319221e294e4f88074"]["climate_mode"] = "heat"
    with patch(HA_PLUGWISE_SMILE_ASYNC_UPDATE, return_value=data):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

        assert (state := hass.states.get("climate.bathroom"))
        assert state.state == "heat"

        # Verify restoration is used when setting the schedule, schedule == "off"
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.bathroom", ATTR_HVAC_MODE: HVACMode.AUTO},
            blocking=True,
        )
        # Verify set_schedule_state was called with the restored schedule
        mock_smile_adam_heat_cool.set_schedule_state.assert_called_with(
            "f871b8c4d63549319221e294e4f88074", STATE_ON, "Badkamer"
        )
        assert mock_smile_adam_heat_cool.set_schedule_state.call_count == 1

    data = mock_smile_adam_heat_cool.async_update.return_value
    data["f871b8c4d63549319221e294e4f88074"]["climate_mode"] = "heat"
    data["f871b8c4d63549319221e294e4f88074"]["select_schedule"] = "Badkamer"
    with patch(HA_PLUGWISE_SMILE_ASYNC_UPDATE, return_value=data):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

        assert (state := hass.states.get("climate.bathroom"))
        assert state.state == "heat"

        # Verify the active schedule is used
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.bathroom", ATTR_HVAC_MODE: HVACMode.AUTO},
            blocking=True,
        )
        assert mock_smile_adam_heat_cool.set_schedule_state.call_count == 2