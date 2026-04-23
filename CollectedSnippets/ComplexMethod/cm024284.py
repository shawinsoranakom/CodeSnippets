async def test_subentry_reconfigure_availablity(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
) -> None:
    """Test the subentry ConfigFlow reconfigure and update device properties."""
    await mqtt_mock_entry()
    config_entry: MockConfigEntry = hass.config_entries.async_entries(mqtt.DOMAIN)[0]
    subentry_id: str
    subentry: ConfigSubentry
    subentry_id, subentry = next(iter(config_entry.subentries.items()))

    expected_availability = {
        "availability_topic": "test/availability",
        "availability_template": "{{ value_json.availability }}",
        "payload_available": "online",
        "payload_not_available": "offline",
    }
    assert subentry.data.get("availability") == expected_availability

    result = await config_entry.start_subentry_reconfigure_flow(hass, subentry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "summary_menu"

    # assert we can set the availability config
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "availability"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "availability"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            "availability_topic": "test/new_availability#invalid_topic",
            "payload_available": "1",
            "payload_not_available": "0",
        },
    )
    assert result["errors"] == {"availability_topic": "invalid_subscribe_topic"}

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            "availability_topic": "test/new_availability",
            "payload_available": "1",
            "payload_not_available": "0",
        },
    )

    # finish reconfigure flow
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "save_changes"},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # Check the availability was updated
    expected_availability = {
        "availability_topic": "test/new_availability",
        "payload_available": "1",
        "payload_not_available": "0",
    }
    assert subentry.data.get("availability") == expected_availability

    # Assert we can reset the availability config
    result = await config_entry.start_subentry_reconfigure_flow(hass, subentry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "summary_menu"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "availability"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "availability"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            "payload_available": "1",
            "payload_not_available": "0",
        },
    )

    # Finish reconfigure flow
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "save_changes"},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # Check the availability was updated
    assert subentry.data.get("availability") == {
        "payload_available": "1",
        "payload_not_available": "0",
    }