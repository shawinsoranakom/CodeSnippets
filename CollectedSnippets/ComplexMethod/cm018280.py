async def test_avmwrapper_passthrough_methods(
    hass: HomeAssistant,
    fc_class_mock,
    fh_class_mock,
    fs_class_mock,
) -> None:
    """Test AvmWrapper helper methods and service wrappers."""

    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    wrapper = entry.runtime_data

    wrapper.device_is_router = False
    assert await wrapper.async_ipv6_active() is False

    assert await wrapper.async_set_wlan_configuration(1, True) == {}
    assert await wrapper.async_set_deflection_enable(1, False) == {}
    assert (
        await wrapper.async_add_port_mapping(
            "WANPPPConnection", {"NewExternalPort": 8080}
        )
        == {}
    )
    assert await wrapper.async_set_allow_wan_access("192.168.178.2", True) == {}
    assert await wrapper.async_wake_on_lan("AA:BB:CC:DD:EE:FF") == {}