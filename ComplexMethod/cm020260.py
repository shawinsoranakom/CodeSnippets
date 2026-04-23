async def test_single_numeric_state_observation(hass: HomeAssistant) -> None:
    """Test a Bayesian sensor with just one numeric_state observation added.

    Combines the config flow and the options flow for a single numeric_state observation.
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
                CONF_NAME: "Nice day",
                CONF_PROBABILITY_THRESHOLD: 51,
                CONF_PRIOR: 20,
            },
        )
        await hass.async_block_till_done()

        # Confirm the next step is the menu
        assert result["step_id"] == OBSERVATION_SELECTOR
        assert result["type"] is FlowResultType.MENU
        assert result["flow_id"] is not None

        # select numeric state observation
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": str(ObservationTypes.NUMERIC_STATE)}
        )
        await hass.async_block_till_done()

        assert result["step_id"] == str(ObservationTypes.NUMERIC_STATE)
        assert result["type"] is FlowResultType.FORM
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ENTITY_ID: "sensor.outside_temperature",
                CONF_ABOVE: 20,
                CONF_BELOW: 35,
                CONF_P_GIVEN_T: 95,
                CONF_P_GIVEN_F: 8,
                CONF_NAME: "20 - 35 outside",
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
        config_entry = result["result"]
        assert config_entry.options == {
            CONF_NAME: "Nice day",
            CONF_PROBABILITY_THRESHOLD: 0.51,
            CONF_PRIOR: 0.2,
        }
        assert len(config_entry.subentries) == 1
        assert list(config_entry.subentries.values())[0].data == {
            CONF_PLATFORM: str(ObservationTypes.NUMERIC_STATE),
            CONF_ENTITY_ID: "sensor.outside_temperature",
            CONF_ABOVE: 20,
            CONF_BELOW: 35,
            CONF_P_GIVEN_T: 0.95,
            CONF_P_GIVEN_F: 0.08,
            CONF_NAME: "20 - 35 outside",
        }

    assert len(mock_setup_entry.mock_calls) == 1