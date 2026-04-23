async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HomematicIPConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the HomematicIP switch from a config entry."""
    hap = config_entry.runtime_data
    entities: list[HomematicipGenericEntity] = [
        HomematicipGroupSwitch(hap, group)
        for group in hap.home.groups
        if isinstance(group, (ExtendedLinkedSwitchingGroup, SwitchingGroup))
    ]
    for device in hap.home.devices:
        if (
            isinstance(device, SwitchMeasuring)
            and getattr(device, "deviceType", None) != DeviceType.BRAND_SWITCH_MEASURING
        ):
            entities.append(HomematicipSwitchMeasuring(hap, device))
        elif isinstance(
            device,
            (
                WiredSwitch4,
                WiredSwitch8,
                OpenCollector8Module,
                StatusBoard8,
                BrandSwitch2,
                PrintedCircuitBoardSwitch2,
                HeatingSwitch2,
                MultiIOBox,
                MotionDetectorSwitchOutdoor,
                DinRailSwitch,
                DinRailSwitch4,
                WiredInput32,
                WiredInputSwitch6,
            ),
        ):
            channel_indices = [
                ch.index
                for ch in device.functionalChannels
                if ch.functionalChannelType
                in (
                    FunctionalChannelType.SWITCH_CHANNEL,
                    FunctionalChannelType.MULTI_MODE_INPUT_SWITCH_CHANNEL,
                )
            ]
            entities.extend(
                HomematicipMultiSwitch(hap, device, channel=channel)
                for channel in channel_indices
            )

        elif isinstance(
            device,
            (
                PlugableSwitch,
                PrintedCircuitBoardSwitchBattery,
                FullFlushInputSwitch,
            ),
        ):
            entities.append(HomematicipSwitch(hap, device))

    async_add_entities(entities)