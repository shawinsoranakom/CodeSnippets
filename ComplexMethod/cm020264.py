async def test_invalid_configs(hass: HomeAssistant) -> None:
    """Test that invalid configs are refused."""
    with patch(
        "homeassistant.components.bayesian.async_setup_entry", return_value=True
    ):
        result0 = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result0["step_id"] == USER
        assert result0["type"] is FlowResultType.FORM

        # priors should never be Zero, because then the sensor can never return 'on'
        with pytest.raises(vol.Invalid) as excinfo:
            result = await hass.config_entries.flow.async_configure(
                result0["flow_id"],
                {
                    CONF_NAME: "Office occupied",
                    CONF_PROBABILITY_THRESHOLD: 50,
                    CONF_PRIOR: 0,
                },
            )
        assert CONF_PRIOR in excinfo.value.path
        assert excinfo.value.error_message == "extreme_prior_error"

        # priors should never be 100% because then the sensor can never be 'off'
        with pytest.raises(vol.Invalid) as excinfo:
            result = await hass.config_entries.flow.async_configure(
                result0["flow_id"],
                {
                    CONF_NAME: "Office occupied",
                    CONF_PROBABILITY_THRESHOLD: 50,
                    CONF_PRIOR: 100,
                },
            )
        assert CONF_PRIOR in excinfo.value.path
        assert excinfo.value.error_message == "extreme_prior_error"

        # Threshold should never be 100% because then the sensor can never be 'on'
        with pytest.raises(vol.Invalid) as excinfo:
            result = await hass.config_entries.flow.async_configure(
                result0["flow_id"],
                {
                    CONF_NAME: "Office occupied",
                    CONF_PROBABILITY_THRESHOLD: 100,
                    CONF_PRIOR: 50,
                },
            )
        assert CONF_PROBABILITY_THRESHOLD in excinfo.value.path
        assert excinfo.value.error_message == "extreme_threshold_error"

        # Threshold should never be 0 because then the sensor can never be 'off'
        with pytest.raises(vol.Invalid) as excinfo:
            result = await hass.config_entries.flow.async_configure(
                result0["flow_id"],
                {
                    CONF_NAME: "Office occupied",
                    CONF_PROBABILITY_THRESHOLD: 0,
                    CONF_PRIOR: 50,
                },
            )
        assert CONF_PROBABILITY_THRESHOLD in excinfo.value.path
        assert excinfo.value.error_message == "extreme_threshold_error"

        # Now lets submit a valid config so we can test the observation flows
        result = await hass.config_entries.flow.async_configure(
            result0["flow_id"],
            {
                CONF_NAME: "Office occupied",
                CONF_PROBABILITY_THRESHOLD: 50,
                CONF_PRIOR: 30,
            },
        )
        await hass.async_block_till_done()
        assert result.get("errors") is None

        # Confirm the next step is the menu
        assert result["step_id"] == OBSERVATION_SELECTOR
        assert result["type"] is FlowResultType.MENU
        assert result["flow_id"] is not None

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": str(ObservationTypes.STATE)}
        )
        await hass.async_block_till_done()

        assert result["step_id"] == str(ObservationTypes.STATE)
        assert result["type"] is FlowResultType.FORM

        # Observations with a probability of 0 will create certainties
        with pytest.raises(vol.Invalid) as excinfo:
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_ENTITY_ID: "sensor.work_laptop",
                    CONF_TO_STATE: "on",
                    CONF_P_GIVEN_T: 0,
                    CONF_P_GIVEN_F: 60,
                    CONF_NAME: "Work laptop on network",
                },
            )
        assert CONF_P_GIVEN_T in excinfo.value.path
        assert excinfo.value.error_message == "extreme_prob_given_error"

        # Observations with a probability of 1 will create certainties
        with pytest.raises(vol.Invalid) as excinfo:
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_ENTITY_ID: "sensor.work_laptop",
                    CONF_TO_STATE: "on",
                    CONF_P_GIVEN_T: 60,
                    CONF_P_GIVEN_F: 100,
                    CONF_NAME: "Work laptop on network",
                },
            )
        assert CONF_P_GIVEN_F in excinfo.value.path
        assert excinfo.value.error_message == "extreme_prob_given_error"

        # Observations with equal probabilities have no effect
        # Try with a ObservationTypes.STATE observation
        current_step = result["step_id"]
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ENTITY_ID: "sensor.work_laptop",
                CONF_TO_STATE: "on",
                CONF_P_GIVEN_T: 60,
                CONF_P_GIVEN_F: 60,
                CONF_NAME: "Work laptop on network",
            },
        )
        await hass.async_block_till_done()
        assert result["step_id"] == current_step
        assert result["errors"] == {"base": "equal_probabilities"}

        # now submit a valid result
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ENTITY_ID: "sensor.work_laptop",
                CONF_TO_STATE: "on",
                CONF_P_GIVEN_T: 60,
                CONF_P_GIVEN_F: 70,
                CONF_NAME: "Work laptop on network",
            },
        )
        await hass.async_block_till_done()
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": str(ObservationTypes.NUMERIC_STATE)}
        )

        await hass.async_block_till_done()
        current_step = result["step_id"]
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ENTITY_ID: "sensor.office_illuminance_lux",
                CONF_ABOVE: 40,
                CONF_P_GIVEN_T: 85,
                CONF_P_GIVEN_F: 85,
                CONF_NAME: "Office is bright",
            },
        )
        await hass.async_block_till_done()
        assert result["step_id"] == current_step
        assert result["errors"] == {"base": "equal_probabilities"}

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ENTITY_ID: "sensor.office_illuminance_lux",
                CONF_ABOVE: 40,
                CONF_P_GIVEN_T: 85,
                CONF_P_GIVEN_F: 10,
                CONF_NAME: "Office is bright",
            },
        )
        await hass.async_block_till_done()
        # Try with a ObservationTypes.TEMPLATE observation
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": str(ObservationTypes.TEMPLATE)}
        )

        await hass.async_block_till_done()
        current_step = result["step_id"]
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_VALUE_TEMPLATE: "{{ is_state('device_tracker.paulus', 'not_home') }}",
                CONF_P_GIVEN_T: 50,
                CONF_P_GIVEN_F: 50,
                CONF_NAME: "Paulus not home",
            },
        )
        await hass.async_block_till_done()
        assert result["step_id"] == current_step
        assert result["errors"] == {"base": "equal_probabilities"}