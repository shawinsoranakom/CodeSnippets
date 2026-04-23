async def test_single_state_observation(hass: HomeAssistant) -> None:
    """Test a Bayesian sensor with just one state observation added.

    This test combines the config flow for a single state observation.
    """

    with patch(
        "homeassistant.components.bayesian.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["step_id"] == USER
        assert result["type"] is FlowResultType.FORM

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Anyone home",
                CONF_PROBABILITY_THRESHOLD: 50,
                CONF_PRIOR: 66,
                CONF_DEVICE_CLASS: "occupancy",
            },
        )
        await hass.async_block_till_done()

        # Confirm the next step is the menu
        assert result["step_id"] == OBSERVATION_SELECTOR
        assert result["type"] is FlowResultType.MENU
        assert result["flow_id"] is not None
        assert result["menu_options"] == ["state", "numeric_state", "template"]

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": str(ObservationTypes.STATE)}
        )
        await hass.async_block_till_done()

        assert result["step_id"] == str(ObservationTypes.STATE)
        assert result["type"] is FlowResultType.FORM

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ENTITY_ID: "sensor.kitchen_occupancy",
                CONF_TO_STATE: "on",
                CONF_P_GIVEN_T: 40,
                CONF_P_GIVEN_F: 0.5,
                CONF_NAME: "Kitchen Motion",
            },
        )

        assert result["step_id"] == OBSERVATION_SELECTOR
        assert result["type"] is FlowResultType.MENU
        assert result["flow_id"] is not None
        assert result["menu_options"] == [
            "state",
            "numeric_state",
            "template",
            "finish",
        ]

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": "finish"}
        )
        await hass.async_block_till_done()

        entry_id = result["result"].entry_id
        config_entry = hass.config_entries.async_get_entry(entry_id)
        assert config_entry is not None
        assert type(config_entry) is ConfigEntry
        assert config_entry.version == 1
        assert config_entry.options == {
            CONF_NAME: "Anyone home",
            CONF_PROBABILITY_THRESHOLD: 0.5,
            CONF_PRIOR: 0.66,
            CONF_DEVICE_CLASS: "occupancy",
        }
        assert len(config_entry.subentries) == 1
        assert list(config_entry.subentries.values())[0].data == {
            CONF_PLATFORM: CONF_STATE,
            CONF_ENTITY_ID: "sensor.kitchen_occupancy",
            CONF_TO_STATE: "on",
            CONF_P_GIVEN_T: 0.4,
            CONF_P_GIVEN_F: 0.005,
            CONF_NAME: "Kitchen Motion",
        }

    assert len(mock_setup_entry.mock_calls) == 1