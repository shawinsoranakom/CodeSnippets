async def test_process_before_send(hass: HomeAssistant) -> None:
    """Test regular use of the Sentry process before sending function."""
    hass.config.components.add("puppies")
    hass.config.components.add("a_integration")

    # These should not show up in the result.
    hass.config.components.add("puppies.light")
    hass.config.components.add("auth")

    result = process_before_send(
        hass,
        options={},
        channel="test",
        huuid="12345",
        system_info={"installation_type": "pytest"},
        custom_components=["ironing_robot", "fridge_opener"],
        event={},
        hint={},
    )

    assert result
    assert result["tags"]
    assert result["contexts"]
    assert result["contexts"]

    ha_context = result["contexts"]["Home Assistant"]
    assert ha_context["channel"] == "test"
    assert ha_context["custom_components"] == "fridge_opener\nironing_robot"
    assert ha_context["integrations"] == "a_integration\npuppies"

    tags = result["tags"]
    assert tags["channel"] == "test"
    assert tags["uuid"] == "12345"
    assert tags["installation_type"] == "pytest"

    user = result["user"]
    assert user["id"] == "12345"