async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HabiticaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the habitica sensors."""

    coordinator = config_entry.runtime_data

    async_add_entities(
        HabiticaSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS + SENSOR_DESCRIPTIONS_COMMON
    )

    if party := coordinator.data.user.party.id:
        party_coordinator = hass.data[HABITICA_KEY][party]
        async_add_entities(
            HabiticaPartySensor(
                party_coordinator,
                config_entry,
                description,
                coordinator.content,
            )
            for description in SENSOR_DESCRIPTIONS_PARTY
        )
        for subentry_id, subentry in config_entry.subentries.items():
            if (
                subentry.unique_id
                and UUID(subentry.unique_id) in party_coordinator.data.members
            ):
                async_add_entities(
                    [
                        HabiticaPartyMemberSensor(
                            coordinator,
                            party_coordinator,
                            description,
                            subentry,
                        )
                        for description in SENSOR_DESCRIPTIONS_COMMON
                    ],
                    config_subentry_id=subentry_id,
                )