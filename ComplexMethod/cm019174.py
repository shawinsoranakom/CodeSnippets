async def test_coordinator_disabling_updates_for_appliance(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
) -> None:
    """Test coordinator disables appliance updates on frequent connect/paired events.

    A repair issue should be created when the updates are disabled.
    When the user confirms the issue the updates should be enabled again.
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
            for _ in range(6)
        ]
    )
    await hass.async_block_till_done()

    freezer.tick(timedelta(minutes=10))
    await client.add_events(
        [
            EventMessage(
                appliance_ha_id,
                EventType.CONNECTED,
                data=ArrayOfEvents([]),
            )
            for _ in range(2)
        ]
    )
    await hass.async_block_till_done()

    # At this point, the updates have been blocked because
    # 6 + 2 connected events have been received in less than an hour

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

    assert hass.states.is_state("switch.dishwasher_power", STATE_ON)

    # After 55 minutes, the updates should be enabled again
    # because one hour has passed since the first connect events,
    # so there are 2 connected events in the execution_tracker
    freezer.tick(timedelta(minutes=55))
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

    # If more connect events are sent, it should be blocked again
    await client.add_events(
        [
            EventMessage(
                appliance_ha_id,
                EventType.CONNECTED,
                data=ArrayOfEvents([]),
            )
            for _ in range(5)  # 2 + 1 + 5 = 8 connect events in less than an hour
        ]
    )
    await hass.async_block_till_done()
    client.get_settings = get_settings_original_side_effect
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