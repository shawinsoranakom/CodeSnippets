async def test_adam_3_climate_entity_attributes(
    hass: HomeAssistant,
    mock_smile_adam_heat_cool: MagicMock,
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test creation of adam climate device environment."""
    mock_restore_cache_with_extra_data(
        hass,
        [
            (
                State("climate.living_room", "heat"),
                PlugwiseClimateExtraStoredData(
                    last_active_schedule="Weekschema",
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

    state = hass.states.get("climate.living_room")
    assert state
    assert state.state == HVACMode.COOL
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.COOLING
    assert state.attributes[ATTR_HVAC_MODES] == [
        HVACMode.OFF,
        HVACMode.AUTO,
        HVACMode.HEAT,
        HVACMode.COOL,
    ]
    data = mock_smile_adam_heat_cool.async_update.return_value
    data["da224107914542988a88561b4452b0f6"]["select_regulation_mode"] = "heating"
    data["f2bf9048bef64cc5b6d5110154e33c81"]["climate_mode"] = "heat"
    data["f2bf9048bef64cc5b6d5110154e33c81"]["control_state"] = HVACAction.HEATING
    data["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"]["cooling_state"] = False
    data["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"]["heating_state"] = True
    with patch(HA_PLUGWISE_SMILE_ASYNC_UPDATE, return_value=data):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

        state = hass.states.get("climate.living_room")
        assert state
        assert state.state == HVACMode.HEAT
        assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.HEATING
        assert state.attributes[ATTR_HVAC_MODES] == [
            HVACMode.OFF,
            HVACMode.AUTO,
            HVACMode.HEAT,
            HVACMode.COOL,
        ]

    data = mock_smile_adam_heat_cool.async_update.return_value
    data["da224107914542988a88561b4452b0f6"]["select_regulation_mode"] = "cooling"
    data["f2bf9048bef64cc5b6d5110154e33c81"]["climate_mode"] = "cool"
    data["f2bf9048bef64cc5b6d5110154e33c81"]["control_state"] = HVACAction.COOLING
    data["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"]["cooling_state"] = True
    data["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"]["heating_state"] = False
    with patch(HA_PLUGWISE_SMILE_ASYNC_UPDATE, return_value=data):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

        state = hass.states.get("climate.living_room")
        assert state
        assert state.state == HVACMode.COOL
        assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.COOLING
        assert state.attributes[ATTR_HVAC_MODES] == [
            HVACMode.OFF,
            HVACMode.AUTO,
            HVACMode.HEAT,
            HVACMode.COOL,
        ]

    data = mock_smile_adam_heat_cool.async_update.return_value
    data["da224107914542988a88561b4452b0f6"]["select_regulation_mode"] = "off"
    data["f2bf9048bef64cc5b6d5110154e33c81"]["climate_mode"] = "off"
    data["f2bf9048bef64cc5b6d5110154e33c81"]["control_state"] = HVACAction.OFF
    data["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"]["cooling_state"] = True
    data["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"]["heating_state"] = False
    with patch(HA_PLUGWISE_SMILE_ASYNC_UPDATE, return_value=data):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

        assert (state := hass.states.get("climate.living_room"))
        assert state.state == "off"
        assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.OFF
        assert state.attributes[ATTR_HVAC_MODES] == [
            HVACMode.OFF,
            HVACMode.AUTO,
            HVACMode.HEAT,
            HVACMode.COOL,
        ]
        # Test setting regulation_mode to cooling, from off, ignoring the restored previous_action_mode
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.living_room", ATTR_HVAC_MODE: HVACMode.COOL},
            blocking=True,
        )
        # Verify set_regulation_mode was called with the user-selected HVACMode
        mock_smile_adam_heat_cool.set_regulation_mode.assert_called_with(
            "cooling",
        )

    data = mock_smile_adam_heat_cool.async_update.return_value
    data["da224107914542988a88561b4452b0f6"]["select_regulation_mode"] = "off"
    data["f871b8c4d63549319221e294e4f88074"]["climate_mode"] = "off"
    data["f871b8c4d63549319221e294e4f88074"]["control_state"] = HVACAction.OFF
    data["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"]["cooling_state"] = True
    data["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"]["heating_state"] = False
    with patch(HA_PLUGWISE_SMILE_ASYNC_UPDATE, return_value=data):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

        assert (state := hass.states.get("climate.bathroom"))
        assert state.state == "off"
        assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.OFF
        assert state.attributes[ATTR_HVAC_MODES] == [
            HVACMode.OFF,
            HVACMode.AUTO,
            HVACMode.HEAT,
            HVACMode.COOL,
        ]
        # Test setting to AUTO, from OFF
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.bathroom", ATTR_HVAC_MODE: HVACMode.AUTO},
            blocking=True,
        )
        # Verify set_regulation_mode was called with the user-selected HVACMode
        mock_smile_adam_heat_cool.set_regulation_mode.assert_called_with(
            "cooling",
        )
        # And set_schedule_state was called with the restored last_active_schedule
        mock_smile_adam_heat_cool.set_schedule_state.assert_called_with(
            "f871b8c4d63549319221e294e4f88074",
            STATE_ON,
            "Badkamer",
        )