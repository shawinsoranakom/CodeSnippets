async def test_reconfiguring_observations(hass: HomeAssistant) -> None:
    """Test editing observations through options flow, once of each of the 3 types."""
    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_NAME: "Office occupied",
            CONF_PROBABILITY_THRESHOLD: 0.5,
            CONF_PRIOR: 0.15,
            CONF_DEVICE_CLASS: "occupancy",
        },
        subentries_data=[
            ConfigSubentryDataWithId(
                data=MappingProxyType(
                    {
                        CONF_PLATFORM: str(ObservationTypes.NUMERIC_STATE),
                        CONF_ENTITY_ID: "sensor.office_illuminance_lux",
                        CONF_ABOVE: 40,
                        CONF_P_GIVEN_T: 0.85,
                        CONF_P_GIVEN_F: 0.45,
                        CONF_NAME: "Office is bright",
                    }
                ),
                subentry_id="01JXCPHRM64Y84GQC58P5EKVHY",
                subentry_type="observation",
                title="Office is bright",
                unique_id=None,
            ),
            ConfigSubentryDataWithId(
                data=MappingProxyType(
                    {
                        CONF_PLATFORM: str(ObservationTypes.STATE),
                        CONF_ENTITY_ID: "sensor.work_laptop",
                        CONF_TO_STATE: "on",
                        CONF_P_GIVEN_T: 0.6,
                        CONF_P_GIVEN_F: 0.2,
                        CONF_NAME: "Work laptop on network",
                    },
                ),
                subentry_id="13TCPHRM64Y84GQC58P5EKTHF",
                subentry_type="observation",
                title="Work laptop on network",
                unique_id=None,
            ),
            ConfigSubentryDataWithId(
                data=MappingProxyType(
                    {
                        CONF_PLATFORM: str(ObservationTypes.TEMPLATE),
                        CONF_VALUE_TEMPLATE: '{% set current_time = now().time() %}\n{% set start_time = strptime("07:00", "%H:%M").time() %}\n{% set end_time = strptime("18:30", "%H:%M").time() %}\n{% if start_time <= current_time <= end_time %}\nTrue\n{% else %}\nFalse\n{% endif %}',
                        CONF_P_GIVEN_T: 0.45,
                        CONF_P_GIVEN_F: 0.05,
                        CONF_NAME: "Daylight hours",
                    }
                ),
                subentry_id="27TCPHRM64Y84GQC58P5EIES",
                subentry_type="observation",
                title="Daylight hours",
                unique_id=None,
            ),
        ],
        title="Office occupied",
    )

    # Set up the mock entry
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set("sensor.office_illuminance_lux", 50)

    # select a subentry for reconfiguration
    result = await config_entry.start_subentry_reconfigure_flow(
        hass, subentry_id="13TCPHRM64Y84GQC58P5EKTHF"
    )
    await hass.async_block_till_done()

    # confirm the first page is the form for editing the observation
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["description_placeholders"]["parent_sensor_name"] == "Office occupied"
    assert result["description_placeholders"]["device_class_on"] == "Detected"
    assert result["description_placeholders"]["device_class_off"] == "Clear"

    # Edit all settings
    await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_ENTITY_ID: "sensor.desktop",
            CONF_TO_STATE: "on",
            CONF_P_GIVEN_T: 70,
            CONF_P_GIVEN_F: 12,
            CONF_NAME: "Desktop on network",
        },
    )
    await hass.async_block_till_done()

    # Confirm the changes to the state config
    assert hass.config_entries.async_get_entry(config_entry.entry_id).options == {
        CONF_NAME: "Office occupied",
        CONF_PROBABILITY_THRESHOLD: 0.5,
        CONF_PRIOR: 0.15,
        CONF_DEVICE_CLASS: "occupancy",
    }
    observations = [
        dict(subentry.data)
        for subentry in hass.config_entries.async_get_entry(
            config_entry.entry_id
        ).subentries.values()
    ]
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
            CONF_ENTITY_ID: "sensor.desktop",
            CONF_TO_STATE: "on",
            CONF_P_GIVEN_T: 0.7,
            CONF_P_GIVEN_F: 0.12,
            CONF_NAME: "Desktop on network",
        },
        {
            CONF_PLATFORM: str(ObservationTypes.TEMPLATE),
            CONF_VALUE_TEMPLATE: '{% set current_time = now().time() %}\n{% set start_time = strptime("07:00", "%H:%M").time() %}\n{% set end_time = strptime("18:30", "%H:%M").time() %}\n{% if start_time <= current_time <= end_time %}\nTrue\n{% else %}\nFalse\n{% endif %}',
            CONF_P_GIVEN_T: 0.45,
            CONF_P_GIVEN_F: 0.05,
            CONF_NAME: "Daylight hours",
        },
    ]

    # Next test editing a numeric_state observation
    # select the subentry for reconfiguration
    result = await config_entry.start_subentry_reconfigure_flow(
        hass, subentry_id="01JXCPHRM64Y84GQC58P5EKVHY"
    )
    await hass.async_block_till_done()

    # confirm the first page is the form for editing the observation
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    await hass.async_block_till_done()

    # Test an invalid re-configuration
    # This should fail as the probabilities are equal
    current_step = result["step_id"]
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_ENTITY_ID: "sensor.office_illuminance_lumens",
            CONF_ABOVE: 2000,
            CONF_P_GIVEN_T: 80,
            CONF_P_GIVEN_F: 80,
            CONF_NAME: "Office is bright",
        },
    )
    await hass.async_block_till_done()
    assert result["step_id"] == current_step
    assert result["errors"] == {"base": "equal_probabilities"}

    # This should work
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_ENTITY_ID: "sensor.office_illuminance_lumens",
            CONF_ABOVE: 2000,
            CONF_P_GIVEN_T: 80,
            CONF_P_GIVEN_F: 40,
            CONF_NAME: "Office is bright",
        },
    )
    await hass.async_block_till_done()
    assert "errors" not in result

    # Confirm the changes to the state config
    assert hass.config_entries.async_get_entry(config_entry.entry_id).options == {
        CONF_NAME: "Office occupied",
        CONF_PROBABILITY_THRESHOLD: 0.5,
        CONF_PRIOR: 0.15,
        CONF_DEVICE_CLASS: "occupancy",
    }
    observations = [
        dict(subentry.data)
        for subentry in hass.config_entries.async_get_entry(
            config_entry.entry_id
        ).subentries.values()
    ]
    assert observations == [
        {
            CONF_PLATFORM: str(ObservationTypes.NUMERIC_STATE),
            CONF_ENTITY_ID: "sensor.office_illuminance_lumens",
            CONF_ABOVE: 2000,
            CONF_P_GIVEN_T: 0.8,
            CONF_P_GIVEN_F: 0.4,
            CONF_NAME: "Office is bright",
        },
        {
            CONF_PLATFORM: str(ObservationTypes.STATE),
            CONF_ENTITY_ID: "sensor.desktop",
            CONF_TO_STATE: "on",
            CONF_P_GIVEN_T: 0.7,
            CONF_P_GIVEN_F: 0.12,
            CONF_NAME: "Desktop on network",
        },
        {
            CONF_PLATFORM: str(ObservationTypes.TEMPLATE),
            CONF_VALUE_TEMPLATE: '{% set current_time = now().time() %}\n{% set start_time = strptime("07:00", "%H:%M").time() %}\n{% set end_time = strptime("18:30", "%H:%M").time() %}\n{% if start_time <= current_time <= end_time %}\nTrue\n{% else %}\nFalse\n{% endif %}',
            CONF_P_GIVEN_T: 0.45,
            CONF_P_GIVEN_F: 0.05,
            CONF_NAME: "Daylight hours",
        },
    ]

    # Next test editing a template observation
    # select the subentry for reconfiguration
    result = await config_entry.start_subentry_reconfigure_flow(
        hass, subentry_id="27TCPHRM64Y84GQC58P5EIES"
    )
    await hass.async_block_till_done()

    # confirm the first page is the form for editing the observation
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    await hass.async_block_till_done()

    await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_VALUE_TEMPLATE: """
{% set current_time = now().time() %}
{% set start_time = strptime("07:00", "%H:%M").time() %}
{% set end_time = strptime("17:30", "%H:%M").time() %}
{% if start_time <= current_time <= end_time %}
True
{% else %}
False
{% endif %}
""",  # changed the end_time
            CONF_P_GIVEN_T: 55,
            CONF_P_GIVEN_F: 13,
            CONF_NAME: "Office hours",
        },
    )
    await hass.async_block_till_done()
    # Confirm the changes to the state config
    assert hass.config_entries.async_get_entry(config_entry.entry_id).options == {
        CONF_NAME: "Office occupied",
        CONF_PROBABILITY_THRESHOLD: 0.5,
        CONF_PRIOR: 0.15,
        CONF_DEVICE_CLASS: "occupancy",
    }
    observations = [
        dict(subentry.data)
        for subentry in hass.config_entries.async_get_entry(
            config_entry.entry_id
        ).subentries.values()
    ]
    assert observations == [
        {
            CONF_PLATFORM: str(ObservationTypes.NUMERIC_STATE),
            CONF_ENTITY_ID: "sensor.office_illuminance_lumens",
            CONF_ABOVE: 2000,
            CONF_P_GIVEN_T: 0.8,
            CONF_P_GIVEN_F: 0.4,
            CONF_NAME: "Office is bright",
        },
        {
            CONF_PLATFORM: str(ObservationTypes.STATE),
            CONF_ENTITY_ID: "sensor.desktop",
            CONF_TO_STATE: "on",
            CONF_P_GIVEN_T: 0.7,
            CONF_P_GIVEN_F: 0.12,
            CONF_NAME: "Desktop on network",
        },
        {
            CONF_PLATFORM: str(ObservationTypes.TEMPLATE),
            CONF_VALUE_TEMPLATE: '{% set current_time = now().time() %}\n{% set start_time = strptime("07:00", "%H:%M").time() %}\n{% set end_time = strptime("17:30", "%H:%M").time() %}\n{% if start_time <= current_time <= end_time %}\nTrue\n{% else %}\nFalse\n{% endif %}',
            CONF_P_GIVEN_T: 0.55,
            CONF_P_GIVEN_F: 0.13,
            CONF_NAME: "Office hours",
        },
    ]