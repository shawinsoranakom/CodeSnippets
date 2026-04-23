async def test_wait_for_port_to_free(
    hass: HomeAssistant,
    hk_driver,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test we wait for the port to free before declaring unload success."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: BRIDGE_NAME, CONF_PORT: DEFAULT_PORT},
        options={},
    )
    entry.add_to_hass(hass)

    with (
        patch("pyhap.accessory_driver.AccessoryDriver.async_start"),
        patch(f"{PATH_HOMEKIT}.HomeKit.async_stop"),
        patch(
            f"{PATH_HOMEKIT}.async_port_is_available", return_value=True
        ) as port_mock,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert "Waiting for the HomeKit server to shutdown" not in caplog.text
        assert port_mock.called

    with (
        patch("pyhap.accessory_driver.AccessoryDriver.async_start"),
        patch(f"{PATH_HOMEKIT}.HomeKit.async_stop"),
        patch.object(homekit_base, "PORT_CLEANUP_CHECK_INTERVAL_SECS", 0),
        patch(
            f"{PATH_HOMEKIT}.async_port_is_available", return_value=False
        ) as port_mock,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert "Waiting for the HomeKit server to shutdown" in caplog.text
        assert port_mock.called