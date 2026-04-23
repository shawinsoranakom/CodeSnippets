async def test_options_flow_devices_preserved_when_advanced_off(
    port_mock, hass: HomeAssistant
) -> None:
    """Test devices are preserved if they were added in advanced mode but it was turned off."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: "mock_name", CONF_PORT: 12345},
        options={
            "devices": ["1fabcabcabcabcabcabcabcabcabc"],
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

        hass.states.async_set("climate.old", "off")
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(
            config_entry.entry_id, context={"show_advanced_options": False}
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

        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "entities": ["climate.old"],
            },
        )

        assert result2["type"] is FlowResultType.CREATE_ENTRY
        assert config_entry.options == {
            "devices": ["1fabcabcabcabcabcabcabcabcabc"],
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
        await hass.async_block_till_done()