async def test_reload_removes_legacy_deprecation(
    hass: HomeAssistant, issue_registry: ir.IssueRegistry
) -> None:
    """Test that we can reload and remove all template sensors."""
    hass.states.async_set("sensor.test_sensor", "old")
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 4
    assert hass.states.get("sensor.state").state == "old"
    assert hass.states.get("sensor.state2").state == "old"
    assert hass.states.get("sensor.state3").state == "old"

    assert len(issue_registry.issues) == 3

    await async_yaml_patch_helper(hass, "legacy_template_deprecation.yaml")
    assert len(hass.states.async_all()) == 4
    assert hass.states.get("sensor.state").state == "old"
    assert hass.states.get("sensor.state2").state == "old"
    assert hass.states.get("sensor.state3").state == "old"
    assert len(issue_registry.issues) == 1