def _async_check_entities() -> None:
        nonlocal added_entities

        if (
            coordinator.data.config.configuration_control is ConfigurationControl.LOCAL
            and not added_entities
        ):
            entities: list[AirGradientSelect] = [
                AirGradientSelect(coordinator, description)
                for description in CONTROL_ENTITIES
            ]
            if "I" in model:
                entities.extend(
                    AirGradientSelect(coordinator, description)
                    for description in DISPLAY_SELECT_TYPES
                )
            if "L" in model:
                entities.extend(
                    AirGradientSelect(coordinator, description)
                    for description in LED_BAR_ENTITIES
                )

            async_add_entities(entities)
            added_entities = True
        elif (
            coordinator.data.config.configuration_control
            is not ConfigurationControl.LOCAL
            and added_entities
        ):
            entity_registry = er.async_get(hass)
            for entity_description in (
                DISPLAY_SELECT_TYPES + LED_BAR_ENTITIES + CONTROL_ENTITIES
            ):
                unique_id = f"{coordinator.serial_number}-{entity_description.key}"
                if entity_id := entity_registry.async_get_entity_id(
                    SELECT_DOMAIN, DOMAIN, unique_id
                ):
                    entity_registry.async_remove(entity_id)
            added_entities = False