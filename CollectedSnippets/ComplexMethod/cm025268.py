async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: XboxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Xbox images."""
    coordinator = config_entry.runtime_data.presence
    if TYPE_CHECKING:
        assert config_entry.unique_id
    async_add_entities(
        [
            XboxImageEntity(hass, coordinator, config_entry.unique_id, description)
            for description in IMAGE_DESCRIPTIONS
        ]
    )

    for subentry_id, subentry in config_entry.subentries.items():
        async_add_entities(
            [
                XboxImageEntity(hass, coordinator, subentry.unique_id, description)
                for description in IMAGE_DESCRIPTIONS
                if subentry.unique_id
                and subentry.unique_id in coordinator.data.presence
                and subentry.subentry_type == "friend"
            ],
            config_subentry_id=subentry_id,
        )