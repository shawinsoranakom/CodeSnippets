def add_entities() -> None:
        """Add or remove a skillset based on the player's class."""

        nonlocal skills_added
        buttons = []
        entity_registry = er.async_get(hass)

        for description in CLASS_SKILLS:
            if (
                (coordinator.data.user.stats.lvl or 0) >= 10
                and coordinator.data.user.flags.classSelected
                and not coordinator.data.user.preferences.disableClasses
                and description.class_needed is coordinator.data.user.stats.Class
            ):
                if description.key not in skills_added:
                    buttons.append(HabiticaButton(coordinator, description))
                    skills_added.add(description.key)
            elif description.key in skills_added:
                if entity_id := entity_registry.async_get_entity_id(
                    BUTTON_DOMAIN,
                    DOMAIN,
                    f"{coordinator.config_entry.unique_id}_{description.key}",
                ):
                    entity_registry.async_remove(entity_id)
                skills_added.remove(description.key)

        if buttons:
            async_add_entities(buttons)