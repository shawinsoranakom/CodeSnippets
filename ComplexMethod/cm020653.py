async def test_reload(hass: HomeAssistant) -> None:
    """Test reloading the media player from yaml."""
    hass.states.async_set("input_boolean.test", STATE_OFF)
    hass.states.async_set("media_player.mock1", STATE_OFF)

    templ = (
        '{% if states.input_boolean.test.state == "off" %}on'
        "{% else %}{{ states.media_player.mock1.state }}{% endif %}"
    )

    await async_setup_component(
        hass,
        "media_player",
        {
            "media_player": {
                "platform": "universal",
                "name": "tv",
                "state_template": templ,
            }
        },
    )

    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 3
    await hass.async_start()

    await hass.async_block_till_done()
    assert hass.states.get("media_player.tv").state == STATE_ON

    hass.states.async_set("input_boolean.test", STATE_ON)
    await hass.async_block_till_done()

    assert hass.states.get("media_player.tv").state == STATE_OFF

    hass.states.async_set("media_player.master_bedroom_2", STATE_OFF)
    hass.states.async_set(
        "remote.alexander_master_bedroom",
        STATE_ON,
        {
            "activity_list": ["act1", "act2"],
            "current_activity": "act2",
            "entity_picture": "/local/picture_remote.png",
        },
    )

    yaml_path = get_fixture_path("configuration.yaml", "universal")
    with patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            "universal",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 5

    assert hass.states.get("media_player.tv") is None
    assert hass.states.get("media_player.master_bed_tv").state == "on"
    assert hass.states.get("media_player.master_bed_tv").attributes["source"] == "act2"
    assert (
        hass.states.get("media_player.master_bed_tv").attributes["entity_picture"]
        == "/local/picture_remote.png"
    )
    assert (
        "device_class" not in hass.states.get("media_player.master_bed_tv").attributes
    )
    assert "unique_id" not in hass.states.get("media_player.master_bed_tv").attributes