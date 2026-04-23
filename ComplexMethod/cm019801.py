async def test_class_change(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    habitica: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test removing and adding skills after class change."""
    mage_skills = [
        "button.test_user_chilling_frost",
        "button.test_user_earthquake",
        "button.test_user_ethereal_surge",
    ]
    healer_skills = [
        "button.test_user_healing_light",
        "button.test_user_protective_aura",
        "button.test_user_searing_brightness",
        "button.test_user_blessing",
    ]

    habitica.get_user.return_value = HabiticaUserResponse.from_json(
        await async_load_fixture(hass, "wizard_fixture.json", DOMAIN)
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    for skill in mage_skills:
        assert hass.states.get(skill)

    habitica.get_user.return_value = HabiticaUserResponse.from_json(
        await async_load_fixture(hass, "healer_fixture.json", DOMAIN)
    )
    freezer.tick(timedelta(seconds=60))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    for skill in mage_skills:
        assert not hass.states.get(skill)

    for skill in healer_skills:
        assert hass.states.get(skill)