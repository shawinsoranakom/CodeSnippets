async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HomematicIPConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the HomematicIP cover from a config entry."""
    hap = config_entry.runtime_data
    entities: list[HomematicipGenericEntity] = [
        HomematicipCoverShutterGroup(hap, group)
        for group in hap.home.groups
        if isinstance(group, ExtendedLinkedShutterGroup)
    ]
    for device in hap.home.devices:
        if isinstance(device, BlindModule):
            entities.append(HomematicipBlindModule(hap, device))
        elif isinstance(device, (DinRailBlind4, WiredDinRailBlind4)):
            entities.extend(
                HomematicipMultiCoverSlats(hap, device, channel=channel)
                for channel in range(1, 5)
            )
        elif isinstance(device, FullFlushBlind):
            entities.append(HomematicipCoverSlats(hap, device))
        elif isinstance(device, FullFlushShutter):
            entities.append(HomematicipCoverShutter(hap, device))
        elif isinstance(device, (HoermannDrivesModule, GarageDoorModuleTormatic)):
            entities.append(HomematicipGarageDoorModule(hap, device))

    async_add_entities(entities)