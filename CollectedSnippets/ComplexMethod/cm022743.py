async def test_setup_creates_entries_for_accessory_mode_devices(
    hass: HomeAssistant,
) -> None:
    """Test we can setup a new instance and we create entries for accessory mode devices."""
    hass.states.async_set("camera.one", "on")
    hass.states.async_set("camera.existing", "on")
    hass.states.async_set("lock.new", "on")
    hass.states.async_set("media_player.two", "on", {"device_class": "tv"})
    hass.states.async_set("remote.standard", "on")
    hass.states.async_set("remote.activity", "on", {"supported_features": 4})

    bridge_mode_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: "bridge", CONF_PORT: 8001},
        options={
            "mode": "bridge",
            "filter": {
                "include_entities": ["camera.existing"],
            },
        },
    )
    bridge_mode_entry.add_to_hass(hass)
    accessory_mode_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: "accessory", CONF_PORT: 8000},
        options={
            "mode": "accessory",
            "filter": {
                "include_entities": ["camera.existing"],
            },
        },
    )
    accessory_mode_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"include_domains": ["camera", "media_player", "light", "lock", "remote"]},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "pairing"

    with (
        patch(
            "homeassistant.components.homekit.config_flow.async_find_next_available_port",
            return_value=12345,
        ),
        patch(
            "homeassistant.components.homekit.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.homekit.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"][:11] == "HASS Bridge"
    bridge_name = (result3["title"].split(":"))[0]
    assert result3["data"] == {
        "filter": {
            "exclude_domains": [],
            "exclude_entities": [],
            "include_domains": ["media_player", "light", "lock", "remote"],
            "include_entities": [],
        },
        "exclude_accessory_mode": True,
        "mode": "bridge",
        "name": bridge_name,
        "port": 12345,
    }
    assert len(mock_setup.mock_calls) == 1
    #
    # Existing accessory mode entries should get setup but not duplicated
    #
    # 1 - existing accessory for camera.existing
    # 2 - existing bridge for camera.one
    # 3 - new bridge
    # 4 - camera.one in accessory mode
    # 5 - media_player.two in accessory mode
    # 6 - remote.activity in accessory mode
    # 7 - lock.new in accessory mode
    assert len(mock_setup_entry.mock_calls) == 7