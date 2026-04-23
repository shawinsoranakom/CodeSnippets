async def async_test_metering(hass: HomeAssistant, cluster: Cluster, entity_id: str):
    """Test Smart Energy metering sensor."""
    await send_attributes_report(hass, cluster, {1025: 1, 1024: 12345, 1026: 100})
    assert_state(hass, entity_id, "12345.0", None)
    assert hass.states.get(entity_id).attributes["status"] == "NO_ALARMS"
    assert hass.states.get(entity_id).attributes["device_type"] == "Electric Metering"

    await send_attributes_report(hass, cluster, {1024: 12346, "status": 64 + 8})
    assert_state(hass, entity_id, "12346.0", None)

    assert hass.states.get(entity_id).attributes["status"] in (
        "SERVICE_DISCONNECT|POWER_FAILURE",
        "POWER_FAILURE|SERVICE_DISCONNECT",
    )

    await send_attributes_report(
        hass, cluster, {"metering_device_type": 1, "status": 64 + 8}
    )
    assert hass.states.get(entity_id).attributes["status"] in (
        "SERVICE_DISCONNECT|NOT_DEFINED",
        "NOT_DEFINED|SERVICE_DISCONNECT",
    )

    await send_attributes_report(
        hass, cluster, {"metering_device_type": 2, "status": 64 + 8}
    )
    assert hass.states.get(entity_id).attributes["status"] in (
        "SERVICE_DISCONNECT|PIPE_EMPTY",
        "PIPE_EMPTY|SERVICE_DISCONNECT",
    )

    await send_attributes_report(
        hass, cluster, {"metering_device_type": 5, "status": 64 + 8}
    )
    assert hass.states.get(entity_id).attributes["status"] in (
        "SERVICE_DISCONNECT|TEMPERATURE_SENSOR",
        "TEMPERATURE_SENSOR|SERVICE_DISCONNECT",
    )

    # Status for other meter types
    await send_attributes_report(
        hass, cluster, {"metering_device_type": 4, "status": 32}
    )
    assert hass.states.get(entity_id).attributes["status"] in ("<bitmap8.32: 32>", "32")