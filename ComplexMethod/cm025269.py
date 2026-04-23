async def async_setup_entry(
    hass: HomeAssistant,
    entry: XboxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Xbox Live friends."""
    coordinator = entry.runtime_data.presence

    if TYPE_CHECKING:
        assert entry.unique_id
    async_add_entities(
        [
            XboxBinarySensorEntity(coordinator, entry.unique_id, description)
            for description in SENSOR_DESCRIPTIONS
            if check_deprecated_entity(
                hass, entry.unique_id, description, BINARY_SENSOR_DOMAIN
            )
        ]
    )

    for subentry_id, subentry in entry.subentries.items():
        async_add_entities(
            [
                XboxBinarySensorEntity(coordinator, subentry.unique_id, description)
                for description in SENSOR_DESCRIPTIONS
                if subentry.unique_id
                and check_deprecated_entity(
                    hass, subentry.unique_id, description, BINARY_SENSOR_DOMAIN
                )
                and subentry.unique_id in coordinator.data.presence
                and subentry.subentry_type == "friend"
            ],
            config_subentry_id=subentry_id,
        )