async def test_config_entry_reload_when_labs_flag_changes(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_admin_user: MockUser,
    hass_read_only_user: MockUser,
) -> None:
    """Test templates are reloaded when labs flag changes."""
    ws_client = await hass_ws_client(hass)

    template_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "hello",
            "template_type": "sensor",
            "state": "{{ 'foo' }}",
        },
        title="My template",
    )
    template_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(template_config_entry.entry_id)
    await hass.async_block_till_done()
    assert await async_setup_component(hass, labs.DOMAIN, {})

    assert hass.states.get("sensor.hello") is not None
    assert hass.states.get("sensor.hello").state == "foo"

    # Check we reload whenever the labs flag is set, even if it's already enabled
    for enabled, set_state in (
        (True, "beer"),
        (True, "is"),
        (False, "very"),
        (False, "good"),
    ):
        hass.config_entries.async_update_entry(
            template_config_entry,
            options={
                "name": "hello",
                "template_type": "sensor",
                "state": f"{{{{ '{set_state}' }}}}",
            },
        )
        with patch(
            "homeassistant.config.load_yaml_config_file",
            autospec=True,
            return_value={},
        ):
            await ws_client.send_json_auto_id(
                {
                    "type": "labs/update",
                    "domain": "automation",
                    "preview_feature": "new_triggers_conditions",
                    "enabled": enabled,
                }
            )

            msg = await ws_client.receive_json()
            assert msg["success"]
            await hass.async_block_till_done()

        assert hass.states.get("sensor.hello") is not None
        assert hass.states.get("sensor.hello").state == set_state