async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HomematicIPConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the HomematicIP Cloud lights from a config entry."""
    hap = config_entry.runtime_data
    entities: list[HomematicipGenericEntity] = []

    entities.extend(
        HomematicipColorLight(hap, d, ch.index)
        for d in hap.home.devices
        for ch in d.functionalChannels
        if ch.functionalChannelType == FunctionalChannelType.UNIVERSAL_LIGHT_CHANNEL
    )

    for device in hap.home.devices:
        if (
            isinstance(device, SwitchMeasuring)
            and getattr(device, "deviceType", None) == DeviceType.BRAND_SWITCH_MEASURING
        ):
            entities.append(HomematicipLightMeasuring(hap, device))
        if isinstance(device, BrandSwitchNotificationLight):
            device_version = Version(device.firmwareVersion)
            entities.append(HomematicipLight(hap, device))

            entity_class = (
                HomematicipNotificationLightV2
                if device_version > Version("2.0.0")
                else HomematicipNotificationLight
            )

            entities.append(
                entity_class(hap, device, device.topLightChannelIndex, "Top")
            )
            entities.append(
                entity_class(hap, device, device.bottomLightChannelIndex, "Bottom")
            )

        elif isinstance(device, (WiredDimmer3, DinRailDimmer3)):
            entities.extend(
                HomematicipMultiDimmer(hap, device, channel=channel)
                for channel in range(1, 4)
            )
        elif isinstance(
            device,
            (Dimmer, PluggableDimmer, BrandDimmer, FullFlushDimmer),
        ):
            entities.append(HomematicipDimmer(hap, device))
        elif isinstance(device, WiredPushButton):
            optical_channels = sorted(
                (
                    ch
                    for ch in device.functionalChannels
                    if ch.functionalChannelType
                    == FunctionalChannelType.OPTICAL_SIGNAL_CHANNEL
                ),
                key=lambda ch: ch.index,
            )
            for led_number, ch in enumerate(optical_channels, start=1):
                entities.append(
                    HomematicipOpticalSignalLight(hap, device, ch.index, led_number)
                )
        elif isinstance(device, CombinationSignallingDevice):
            entities.append(HomematicipCombinationSignallingLight(hap, device))

    async_add_entities(entities)