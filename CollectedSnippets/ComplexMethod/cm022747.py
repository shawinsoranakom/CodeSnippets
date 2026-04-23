async def test_options_flow_devices(
    port_mock,
    hass: HomeAssistant,
    demo_cleanup,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test devices can be bridged."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: "mock_name", CONF_PORT: 12345},
        options={
            "devices": ["notexist"],
            "filter": {
                "include_domains": [
                    "fan",
                    "humidifier",
                    "vacuum",
                    "media_player",
                    "climate",
                    "alarm_control_panel",
                ],
                "exclude_entities": ["climate.front_gate"],
            },
        },
    )
    config_entry.add_to_hass(hass)

    demo_config_entry = MockConfigEntry(domain="domain")
    demo_config_entry.add_to_hass(hass)

    with patch("homeassistant.components.homekit.HomeKit") as mock_homekit:
        mock_homekit.return_value = homekit = Mock()
        type(homekit).async_start = AsyncMock()
        assert await async_setup_component(hass, "homekit", {"homekit": {}})
        assert await async_setup_component(hass, "homeassistant", {})
        assert await async_setup_component(hass, "demo", {"demo": {}})
        assert await async_setup_component(hass, "homekit", {"homekit": {}})

        hass.states.async_set("climate.old", "off")
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(
            config_entry.entry_id, context={"show_advanced_options": True}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "domains": ["fan", "vacuum", "climate"],
                "include_exclude_mode": "exclude",
            },
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "exclude"

        entry = entity_registry.async_get("light.ceiling_lights")
        assert entry is not None
        device_id = entry.device_id

        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "entities": ["climate.old"],
            },
        )

        with patch(
            "homeassistant.components.homekit.async_setup_entry", return_value=True
        ):
            result3 = await hass.config_entries.options.async_configure(
                result2["flow_id"],
                user_input={"devices": [device_id]},
            )

        assert result3["type"] is FlowResultType.CREATE_ENTRY
        assert config_entry.options == {
            "devices": [device_id],
            "mode": "bridge",
            "filter": {
                "exclude_domains": [],
                "exclude_entities": ["climate.old"],
                "include_domains": ["fan", "vacuum", "climate"],
                "include_entities": [],
            },
        }

        await hass.async_block_till_done()
        await hass.config_entries.async_unload(config_entry.entry_id)