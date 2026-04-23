async def test_yaml_import(
    hass: HomeAssistant,
    issue_registry: ir.IssueRegistry,
    mock_london_underground_client,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test a YAML sensor is imported and becomes an operational config entry."""
    # Set up via YAML which will trigger import and set up the config entry
    VALID_CONFIG = {
        "sensor": {
            "platform": "london_underground",
            CONF_LINE: ["Metropolitan", "London Overground"],
        }
    }
    assert await async_setup_component(hass, "sensor", VALID_CONFIG)
    await hass.async_block_till_done()

    # Verify the config entry was created
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    # Verify a warning was issued about YAML deprecation
    assert issue_registry.async_get_issue(HOMEASSISTANT_DOMAIN, "deprecated_yaml")

    # Check the state after setup completes
    state = hass.states.get("sensor.london_underground_metropolitan")
    assert state
    assert state.state == "Good Service"
    assert state.attributes == {
        "Description": "Nothing to report",
        "attribution": "Powered by TfL Open Data",
        "friendly_name": "London Underground Metropolitan",
        "icon": "mdi:subway",
    }

    # Since being renamed London overground is no longer returned by the API
    # So check that we do not import it and that we warn the user
    state = hass.states.get("sensor.london_underground_london_overground")
    assert not state
    assert any(
        "London Overground was removed from the configuration as the line has been divided and renamed"
        in record.message
        for record in caplog.records
    )