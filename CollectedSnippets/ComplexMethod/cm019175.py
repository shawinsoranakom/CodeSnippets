async def test_coordinator_disabling_updates_for_appliance_is_gone_after_entry_reload(
    hass: HomeAssistant,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
) -> None:
    """Test that updates are enabled again after unloading the entry.

    The repair issue should also be deleted.
    """
    appliance_ha_id = "SIEMENS-HCS02DWH1-6BE58C26DCC1"

    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED

    assert hass.states.is_state("switch.dishwasher_power", STATE_ON)

    await client.add_events(
        [
            EventMessage(
                appliance_ha_id,
                EventType.CONNECTED,
                data=ArrayOfEvents([]),
            )
            for _ in range(8)
        ]
    )
    await hass.async_block_till_done()

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED

    get_settings_original_side_effect = client.get_settings.side_effect

    async def get_settings_side_effect(ha_id: str) -> ArrayOfSettings:
        if ha_id == appliance_ha_id:
            return ArrayOfSettings(
                [
                    GetSetting(
                        SettingKey.BSH_COMMON_POWER_STATE,
                        SettingKey.BSH_COMMON_POWER_STATE.value,
                        BSH_POWER_OFF,
                    )
                ]
            )
        return cast(ArrayOfSettings, get_settings_original_side_effect(ha_id))

    client.get_settings = AsyncMock(side_effect=get_settings_side_effect)

    await client.add_events(
        [
            EventMessage(
                appliance_ha_id,
                EventType.CONNECTED,
                data=ArrayOfEvents([]),
            )
        ]
    )
    await hass.async_block_till_done()

    assert hass.states.is_state("switch.dishwasher_power", STATE_OFF)