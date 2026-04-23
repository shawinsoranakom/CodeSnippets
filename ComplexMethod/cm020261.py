async def test_multi_numeric_state_observation(hass: HomeAssistant) -> None:
    """Test a Bayesian sensor with just more than one numeric_state observation added.

    Technically a subset of the tests in test_config_flow() but may help to
    narrow down errors more quickly.
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

        # Confirm the next step is the menu
        assert result["step_id"] == OBSERVATION_SELECTOR
        assert result["type"] is FlowResultType.MENU
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": str(ObservationTypes.NUMERIC_STATE)}
        )
        await hass.async_block_till_done()

        # This should fail as overlapping ranges for the same entity are not allowed
        current_step = result["step_id"]
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ENTITY_ID: "sensor.outside_temperature",
                CONF_ABOVE: 30,
                CONF_BELOW: 40,
                CONF_P_GIVEN_T: 95,
                CONF_P_GIVEN_F: 8,
                CONF_NAME: "30 - 40 outside",
            },
        )
        await hass.async_block_till_done()
        assert result["errors"] == {"base": "overlapping_ranges"}
        assert result["step_id"] == current_step

        # This should fail as above should always be less than below
        current_step = result["step_id"]
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ENTITY_ID: "sensor.outside_temperature",
                CONF_ABOVE: 40,
                CONF_BELOW: 35,
                CONF_P_GIVEN_T: 95,
                CONF_P_GIVEN_F: 8,
                CONF_NAME: "35 - 40 outside",
            },
        )
        await hass.async_block_till_done()
        assert result["step_id"] == current_step
        assert result["errors"] == {"base": "above_below"}

        # This should work
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ENTITY_ID: "sensor.outside_temperature",
                CONF_ABOVE: 35,
                CONF_BELOW: 40,
                CONF_P_GIVEN_T: 70,
                CONF_P_GIVEN_F: 20,
                CONF_NAME: "35 - 40 outside",
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
        assert config_entry.version == 1
        assert config_entry.options == {
            CONF_NAME: "Nice day",
            CONF_PROBABILITY_THRESHOLD: 0.51,
            CONF_PRIOR: 0.2,
        }
        observations = [
            dict(subentry.data) for subentry in config_entry.subentries.values()
        ]
        assert observations == [
            {
                CONF_PLATFORM: str(ObservationTypes.NUMERIC_STATE),
                CONF_ENTITY_ID: "sensor.outside_temperature",
                CONF_ABOVE: 20.0,
                CONF_BELOW: 35.0,
                CONF_P_GIVEN_T: 0.95,
                CONF_P_GIVEN_F: 0.08,
                CONF_NAME: "20 - 35 outside",
            },
            {
                CONF_PLATFORM: str(ObservationTypes.NUMERIC_STATE),
                CONF_ENTITY_ID: "sensor.outside_temperature",
                CONF_ABOVE: 35.0,
                CONF_BELOW: 40.0,
                CONF_P_GIVEN_T: 0.7,
                CONF_P_GIVEN_F: 0.2,
                CONF_NAME: "35 - 40 outside",
            },
        ]

    assert len(mock_setup_entry.mock_calls) == 1