async def test_deprecated_sensor_issue(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_request_status: AsyncMock,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    entity_key: str,
    issue_key: str,
) -> None:
    """Ensure the issue lists automations and scripts referencing a deprecated sensor."""
    issue_registry = ir.async_get(hass)
    unique_id = f"{mock_request_status.return_value['SERIALNO']}_{entity_key}"
    entity_id = entity_registry.async_get_entity_id("sensor", DOMAIN, unique_id)
    assert entity_id

    # No issue yet.
    issue_id = f"{issue_key}_{entity_id}"
    assert issue_registry.async_get_issue(DOMAIN, issue_id) is None

    # Add automations and scripts referencing the deprecated sensor.
    entity_slug = slugify(entity_key)
    automation_object_id = f"apcupsd_auto_{entity_slug}"
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "id": automation_object_id,
                "alias": f"APC UPS automation ({entity_key})",
                "trigger": {"platform": "state", "entity_id": entity_id},
                "action": {
                    "action": "automation.turn_on",
                    "target": {"entity_id": f"automation.{automation_object_id}"},
                },
            }
        },
    )

    assert await async_setup_component(
        hass,
        script.DOMAIN,
        {
            script.DOMAIN: {
                f"apcupsd_script_{entity_slug}": {
                    "alias": f"APC UPS script ({entity_key})",
                    "sequence": [
                        {
                            "condition": "state",
                            "entity_id": entity_id,
                            "state": "on",
                        }
                    ],
                }
            }
        },
    )
    await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    issue = issue_registry.async_get_issue(DOMAIN, issue_id)
    # Redact the device ID in the placeholder for consistency.
    issue.translation_placeholders["device_id"] = "<ANY>"
    assert issue == snapshot

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Assert the issue is no longer present.
    assert not issue_registry.async_get_issue(DOMAIN, issue_id)
    assert len(issue_registry.issues) == 0