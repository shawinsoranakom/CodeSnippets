async def test_create_issue_with_items(
    hass: HomeAssistant,
    devices: AsyncMock,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    issue_registry: ir.IssueRegistry,
    device_id: str,
    suggested_object_id: str,
    issue_string: str,
) -> None:
    """Test we create an issue when an automation or script is using a deprecated entity."""
    entity_id = f"switch.{suggested_object_id}"
    issue_id = f"deprecated_switch_{issue_string}_{entity_id}"

    entity_entry = entity_registry.async_get_or_create(
        SWITCH_DOMAIN,
        DOMAIN,
        f"{device_id}_{MAIN}_{Capability.SWITCH}_{Attribute.SWITCH}_{Attribute.SWITCH}",
        suggested_object_id=suggested_object_id,
        original_name=suggested_object_id,
    )

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "id": "test",
                "alias": "test",
                "trigger": {"platform": "state", "entity_id": entity_id},
                "action": {
                    "action": "automation.turn_on",
                    "target": {
                        "entity_id": "automation.test",
                    },
                },
            }
        },
    )
    assert await async_setup_component(
        hass,
        script.DOMAIN,
        {
            script.DOMAIN: {
                "test": {
                    "sequence": [
                        {
                            "condition": "state",
                            "entity_id": entity_id,
                            "state": "on",
                        },
                    ],
                }
            }
        },
    )

    await setup_integration(hass, mock_config_entry)

    assert hass.states.get(entity_id).state in [STATE_OFF, STATE_ON]

    assert automations_with_entity(hass, entity_id)[0] == "automation.test"
    assert scripts_with_entity(hass, entity_id)[0] == "script.test"

    issue = issue_registry.async_get_issue(DOMAIN, issue_id)
    assert issue is not None
    assert issue.translation_key == f"deprecated_switch_{issue_string}_scripts"
    assert issue.translation_placeholders == {
        "entity_id": entity_id,
        "entity_name": suggested_object_id,
        "items": "- [test](/config/automation/edit/test)\n- [test](/config/script/edit/test)",
    }

    entity_registry.async_update_entity(
        entity_entry.entity_id,
        disabled_by=er.RegistryEntryDisabler.USER,
    )

    await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Assert the issue is no longer present
    assert not issue_registry.async_get_issue(DOMAIN, issue_id)