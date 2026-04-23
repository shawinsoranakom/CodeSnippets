async def test_notify_leaving_zone(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test notifying leaving a zone blueprint."""
    config_entry = MockConfigEntry(domain="fake_integration", data={})
    config_entry.mock_state(hass, ConfigEntryState.LOADED)
    config_entry.add_to_hass(hass)

    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "00:00:00:00:00:01")},
    )

    def set_person_state(state: str, extra: dict[str, Any]) -> None:
        hass.states.async_set(
            "person.test_person", state, {"friendly_name": "Paulus", **extra}
        )

    set_person_state("School", {})

    assert await async_setup_component(
        hass, "zone", {"zone": {"name": "School", "latitude": 1, "longitude": 2}}
    )

    with patch_blueprint(
        "notify_leaving_zone.yaml",
        BUILTIN_BLUEPRINT_FOLDER / "notify_leaving_zone.yaml",
    ):
        assert await async_setup_component(
            hass,
            "automation",
            {
                "automation": {
                    "use_blueprint": {
                        "path": "notify_leaving_zone.yaml",
                        "input": {
                            "person_entity": "person.test_person",
                            "zone_entity": "zone.school",
                            "notify_device": device.id,
                        },
                    }
                }
            },
        )

    with patch(
        "homeassistant.components.mobile_app.device_action.async_call_action_from_config"
    ) as mock_call_action:
        # Leaving zone to no zone
        set_person_state("not_home", {})
        await hass.async_block_till_done()

        assert len(mock_call_action.mock_calls) == 1
        _hass, config, variables, _context = mock_call_action.mock_calls[0][1]
        message_tpl = config.pop("message")
        assert config == {
            "alias": "Notify that a person has left the zone",
            "domain": "mobile_app",
            "type": "notify",
            "device_id": device.id,
        }
        message_tpl.hass = hass
        assert message_tpl.async_render(variables) == "Paulus has left School"

        # Should not increase when we go to another zone
        set_person_state("bla", {})
        await hass.async_block_till_done()

        assert len(mock_call_action.mock_calls) == 1

        # Should not increase when we go into the zone
        set_person_state("School", {})
        await hass.async_block_till_done()

        assert len(mock_call_action.mock_calls) == 1

        # Should not increase when we move in the zone
        set_person_state("School", {"extra_key": "triggers change with same state"})
        await hass.async_block_till_done()

        assert len(mock_call_action.mock_calls) == 1

        # Should increase when leaving zone for another zone
        set_person_state("Just Outside School", {})
        await hass.async_block_till_done()

        assert len(mock_call_action.mock_calls) == 2

        # Verify trigger works
        await hass.services.async_call(
            "automation",
            "trigger",
            {"entity_id": "automation.automation_0"},
            blocking=True,
        )
        assert len(mock_call_action.mock_calls) == 3