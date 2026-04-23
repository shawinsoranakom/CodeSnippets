async def test_legacy_door_tilt_state_repair_issue(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    issue_registry: ir.IssueRegistry,
    client: MagicMock,
    hoppe_ehandle_connectsense_state: NodeDataType,
) -> None:
    """Test a tilt-state legacy entity creates the tilt-state repair issue."""
    node = Node(
        client,
        _set_opening_state_metadata_states(
            hoppe_ehandle_connectsense_state,
            {"0": "Closed", "1": "Open", "2": "Tilted"},
        ),
    )
    client.driver.controller.nodes[node.node_id] = node
    home_id = client.driver.controller.home_id

    entity_entry = entity_registry.async_get_or_create(
        BINARY_SENSOR_DOMAIN,
        DOMAIN,
        f"{home_id}.20-113-0-Access Control-Door state.5633",
        suggested_object_id="ehandle_connectsense_window_door_is_open_in_tilt_position",
        original_name="Window/door is open in tilt position",
    )
    entity_id = entity_entry.entity_id

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "id": "test_automation",
                "alias": "test",
                "trigger": {"platform": "state", "entity_id": entity_id},
                "action": {
                    "action": "automation.turn_on",
                    "target": {"entity_id": "automation.test_automation"},
                },
            }
        },
    )

    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    issue = issue_registry.async_get_issue(
        DOMAIN, f"deprecated_legacy_door_tilt_state.{entity_id}"
    )
    assert issue is not None
    assert issue.translation_key == "deprecated_legacy_door_tilt_state"
    assert issue.translation_placeholders["entity_id"] == entity_id
    assert (
        issue.translation_placeholders["entity_name"]
        == "Window/door is open in tilt position"
    )
    assert (
        issue.translation_placeholders["replacement_entity_id"]
        == "binary_sensor.ehandle_connectsense_tilt"
    )
    assert "test" in issue.translation_placeholders["items"]