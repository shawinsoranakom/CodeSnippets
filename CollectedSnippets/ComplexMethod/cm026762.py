def _async_check_entities() -> None:
        nonlocal added_entities

        if (
            coordinator.data.config.configuration_control is ConfigurationControl.LOCAL
            and not added_entities
        ):
            entities = []
            if "I" in model:
                entities.append(AirGradientNumber(coordinator, DISPLAY_BRIGHTNESS))
            if "L" in model:
                entities.append(AirGradientNumber(coordinator, LED_BAR_BRIGHTNESS))

            async_add_entities(entities)
            added_entities = True
        elif (
            coordinator.data.config.configuration_control
            is not ConfigurationControl.LOCAL
            and added_entities
        ):
            entity_registry = er.async_get(hass)
            for entity_description in (DISPLAY_BRIGHTNESS, LED_BAR_BRIGHTNESS):
                unique_id = f"{coordinator.serial_number}-{entity_description.key}"
                if entity_id := entity_registry.async_get_entity_id(
                    NUMBER_DOMAIN, DOMAIN, unique_id
                ):
                    entity_registry.async_remove(entity_id)
            added_entities = False