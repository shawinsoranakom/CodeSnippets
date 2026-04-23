async def test_remove_party_and_reload(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    habitica: AsyncMock,
    freezer: FrozenDateTimeFactory,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test we leave the party and device/notifiers are removed."""
    group_id = "1e87097c-4c03-4f8c-a475-67cc7da7f409"
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    assert (
        device_registry.async_get_device(
            {(DOMAIN, f"{config_entry.unique_id}_{group_id}")}
        )
        is not None
    )

    assert hass.states.get("notify.test_user_party_chat")
    assert hass.states.get(
        "notify.test_user_private_message_test_partymember_displayname"
    )

    habitica.get_user.return_value = HabiticaUserResponse.from_json(
        await async_load_fixture(hass, "user_no_party.json", DOMAIN)
    )

    freezer.tick(datetime.timedelta(seconds=60))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (
        device_registry.async_get_device(
            {(DOMAIN, f"{config_entry.unique_id}_{group_id}")}
        )
        is None
    )

    assert hass.states.get("notify.test_user_party_chat") is None
    assert (
        hass.states.get("notify.test_user_private_message_test_partymember_displayname")
        is None
    )