async def test_humanify_shelly_click_event_rpc_device(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry, mock_rpc_device: Mock
) -> None:
    """Test humanifying Shelly click event for rpc device."""
    entry = await init_integration(hass, 2)
    device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

    hass.config.components.add("recorder")
    assert await async_setup_component(hass, "logbook", {})
    await hass.async_block_till_done()

    event1, event2 = mock_humanify(
        hass,
        [
            MockRow(
                EVENT_SHELLY_CLICK,
                {
                    ATTR_DEVICE_ID: device.id,
                    ATTR_DEVICE: "shellyplus1pm-12345678",
                    ATTR_CLICK_TYPE: "single_push",
                    ATTR_CHANNEL: 1,
                },
            ),
            MockRow(
                EVENT_SHELLY_CLICK,
                {
                    ATTR_DEVICE_ID: "no_device_id",
                    ATTR_DEVICE: "shellypro4pm-12345678",
                    ATTR_CLICK_TYPE: "btn_down",
                    ATTR_CHANNEL: 2,
                },
            ),
        ],
    )

    assert event1["name"] == "Shelly"
    assert event1["domain"] == DOMAIN
    assert (
        event1["message"]
        == "'single_push' click event for Test name Test input 0 Input was fired"
    )

    assert event2["name"] == "Shelly"
    assert event2["domain"] == DOMAIN
    assert (
        event2["message"]
        == "'btn_down' click event for shellypro4pm-12345678 channel 2 Input was fired"
    )