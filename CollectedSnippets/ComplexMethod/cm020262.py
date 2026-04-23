async def test_single_template_observation(hass: HomeAssistant) -> None:
    """Test a Bayesian sensor with just one template observation added.

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
                CONF_NAME: "Paulus Home",
                CONF_PROBABILITY_THRESHOLD: 90,
                CONF_PRIOR: 50,
                CONF_DEVICE_CLASS: "occupancy",
            },
        )
        await hass.async_block_till_done()

        # Confirm the next step is the menu
        assert result["step_id"] == OBSERVATION_SELECTOR
        assert result["type"] is FlowResultType.MENU
        assert result["flow_id"] is not None

        # Select template observation
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": str(ObservationTypes.TEMPLATE)}
        )
        await hass.async_block_till_done()

        assert result["step_id"] == str(ObservationTypes.TEMPLATE)
        assert result["type"] is FlowResultType.FORM
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_VALUE_TEMPLATE: "{{is_state('device_tracker.paulus','not_home') and ((as_timestamp(now()) - as_timestamp(states.device_tracker.paulus.last_changed)) > 300)}}",
                CONF_P_GIVEN_T: 5,
                CONF_P_GIVEN_F: 99,
                CONF_NAME: "Not seen in last 5 minutes",
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
            CONF_NAME: "Paulus Home",
            CONF_PROBABILITY_THRESHOLD: 0.9,
            CONF_PRIOR: 0.5,
            CONF_DEVICE_CLASS: "occupancy",
        }
        assert len(config_entry.subentries) == 1
        assert list(config_entry.subentries.values())[0].data == {
            CONF_PLATFORM: str(ObservationTypes.TEMPLATE),
            CONF_VALUE_TEMPLATE: "{{is_state('device_tracker.paulus','not_home') and ((as_timestamp(now()) - as_timestamp(states.device_tracker.paulus.last_changed)) > 300)}}",
            CONF_P_GIVEN_T: 0.05,
            CONF_P_GIVEN_F: 0.99,
            CONF_NAME: "Not seen in last 5 minutes",
        }

    assert len(mock_setup_entry.mock_calls) == 1