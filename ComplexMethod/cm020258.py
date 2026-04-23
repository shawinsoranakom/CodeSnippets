async def test_subentry_flow(hass: HomeAssistant) -> None:
    """Test the subentry flow with a full example."""
    with patch(
        "homeassistant.components.bayesian.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        # Set up the initial config entry as a mock to isolate testing of subentry flows
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_NAME: "Office occupied",
                CONF_PROBABILITY_THRESHOLD: 50,
                CONF_PRIOR: 15,
                CONF_DEVICE_CLASS: "occupancy",
            },
        )
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        # Open subentry flow
        result = await hass.config_entries.subentries.async_init(
            (config_entry.entry_id, "observation"),
            context={"source": config_entries.SOURCE_USER},
        )
        # Confirm the next page is the observation type selector
        assert result["step_id"] == "user"
        assert result["type"] is FlowResultType.MENU
        assert result["flow_id"] is not None

        # Set up a numeric state observation first
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"], {"next_step_id": str(ObservationTypes.NUMERIC_STATE)}
        )
        await hass.async_block_till_done()

        assert result["step_id"] == str(ObservationTypes.NUMERIC_STATE)
        assert result["type"] is FlowResultType.FORM

        # Set up a numeric range with only 'Above'
        # Also indirectly tests the conversion of proabilities to fractions
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {
                CONF_ENTITY_ID: "sensor.office_illuminance_lux",
                CONF_ABOVE: 40,
                CONF_P_GIVEN_T: 85,
                CONF_P_GIVEN_F: 45,
                CONF_NAME: "Office is bright",
            },
        )
        await hass.async_block_till_done()

        # Open another subentry flow
        result = await hass.config_entries.subentries.async_init(
            (config_entry.entry_id, "observation"),
            context={"source": config_entries.SOURCE_USER},
        )
        assert result["step_id"] == "user"
        assert result["type"] is FlowResultType.MENU
        assert result["flow_id"] is not None

        # Add a state observation
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"], {"next_step_id": str(ObservationTypes.STATE)}
        )
        await hass.async_block_till_done()

        assert result["step_id"] == str(ObservationTypes.STATE)
        assert result["type"] is FlowResultType.FORM
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {
                CONF_ENTITY_ID: "sensor.work_laptop",
                CONF_TO_STATE: "on",
                CONF_P_GIVEN_T: 60,
                CONF_P_GIVEN_F: 20,
                CONF_NAME: "Work laptop on network",
            },
        )
        await hass.async_block_till_done()

        # Open another subentry flow
        result = await hass.config_entries.subentries.async_init(
            (config_entry.entry_id, "observation"),
            context={"source": config_entries.SOURCE_USER},
        )
        assert result["step_id"] == "user"
        assert result["type"] is FlowResultType.MENU
        assert result["flow_id"] is not None

        # Lastly, add a template observation
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"], {"next_step_id": str(ObservationTypes.TEMPLATE)}
        )
        await hass.async_block_till_done()

        assert result["step_id"] == str(ObservationTypes.TEMPLATE)
        assert result["type"] is FlowResultType.FORM
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {
                CONF_VALUE_TEMPLATE: """
{% set current_time = now().time() %}
{% set start_time = strptime("07:00", "%H:%M").time() %}
{% set end_time = strptime("18:30", "%H:%M").time() %}
{% if start_time <= current_time <= end_time %}
True
{% else %}
False
{% endif %}
                """,
                CONF_P_GIVEN_T: 45,
                CONF_P_GIVEN_F: 5,
                CONF_NAME: "Daylight hours",
            },
        )

        observations = [
            dict(subentry.data) for subentry in config_entry.subentries.values()
        ]
        # assert config_entry["version"] == 1
        assert observations == [
            {
                CONF_PLATFORM: str(ObservationTypes.NUMERIC_STATE),
                CONF_ENTITY_ID: "sensor.office_illuminance_lux",
                CONF_ABOVE: 40,
                CONF_P_GIVEN_T: 0.85,
                CONF_P_GIVEN_F: 0.45,
                CONF_NAME: "Office is bright",
            },
            {
                CONF_PLATFORM: str(ObservationTypes.STATE),
                CONF_ENTITY_ID: "sensor.work_laptop",
                CONF_TO_STATE: "on",
                CONF_P_GIVEN_T: 0.6,
                CONF_P_GIVEN_F: 0.2,
                CONF_NAME: "Work laptop on network",
            },
            {
                CONF_PLATFORM: str(ObservationTypes.TEMPLATE),
                CONF_VALUE_TEMPLATE: '{% set current_time = now().time() %}\n{% set start_time = strptime("07:00", "%H:%M").time() %}\n{% set end_time = strptime("18:30", "%H:%M").time() %}\n{% if start_time <= current_time <= end_time %}\nTrue\n{% else %}\nFalse\n{% endif %}',
                CONF_P_GIVEN_T: 0.45,
                CONF_P_GIVEN_F: 0.05,
                CONF_NAME: "Daylight hours",
            },
        ]

    assert len(mock_setup_entry.mock_calls) == 1