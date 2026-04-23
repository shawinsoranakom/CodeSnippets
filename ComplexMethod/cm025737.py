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