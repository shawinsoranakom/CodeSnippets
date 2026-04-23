async def async_setup_entry(
    hass: HomeAssistant,
    entry: GhostConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Ghost sensors based on a config entry."""
    coordinator = entry.runtime_data.coordinator

    entities: list[GhostSensorEntity | GhostNewsletterSensorEntity] = [
        GhostSensorEntity(coordinator, description, entry) for description in SENSORS
    ]

    # Add revenue sensors only when Stripe is linked.
    if coordinator.data.mrr:
        entities.extend(
            GhostSensorEntity(coordinator, description, entry)
            for description in REVENUE_SENSORS
        )

    async_add_entities(entities)

    # Remove stale newsletter entities left over from previous runs.
    entity_registry = er.async_get(hass)
    prefix = f"{entry.unique_id}_newsletter_"
    active_newsletters = {
        newsletter_id
        for newsletter_id, newsletter in coordinator.data.newsletters.items()
        if newsletter.get("status") == "active"
    }
    for entity_entry in er.async_entries_for_config_entry(
        entity_registry, entry.entry_id
    ):
        if (
            entity_entry.unique_id.startswith(prefix)
            and entity_entry.unique_id[len(prefix) :] not in active_newsletters
        ):
            entity_registry.async_remove(entity_entry.entity_id)

    newsletter_added: set[str] = set()

    @callback
    def _async_update_newsletter_entities() -> None:
        """Add new and remove stale newsletter entities."""
        nonlocal newsletter_added

        active_newsletters = {
            newsletter_id
            for newsletter_id, newsletter in coordinator.data.newsletters.items()
            if newsletter.get("status") == "active"
        }

        new_newsletters = active_newsletters - newsletter_added

        if new_newsletters:
            async_add_entities(
                GhostNewsletterSensorEntity(
                    coordinator,
                    entry,
                    newsletter_id,
                    coordinator.data.newsletters[newsletter_id].get(
                        "name", "Newsletter"
                    ),
                )
                for newsletter_id in new_newsletters
            )
            newsletter_added.update(new_newsletters)

        removed_newsletters = newsletter_added - active_newsletters
        if removed_newsletters:
            entity_registry = er.async_get(hass)
            for newsletter_id in removed_newsletters:
                unique_id = f"{entry.unique_id}_newsletter_{newsletter_id}"
                entity_id = entity_registry.async_get_entity_id(
                    Platform.SENSOR, DOMAIN, unique_id
                )
                if entity_id:
                    entity_registry.async_remove(entity_id)
            newsletter_added -= removed_newsletters

    _async_update_newsletter_entities()
    entry.async_on_unload(
        coordinator.async_add_listener(_async_update_newsletter_entities)
    )