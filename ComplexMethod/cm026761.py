def _check_entities() -> None:
        nonlocal added_entities

        if (
            coordinator.data.config.configuration_control is ConfigurationControl.LOCAL
            and not added_entities
        ):
            entities = [AirGradientButton(coordinator, CO2_CALIBRATION)]
            if "L" in model:
                entities.append(AirGradientButton(coordinator, LED_BAR_TEST))

            async_add_entities(entities)
            added_entities = True
        elif (
            coordinator.data.config.configuration_control
            is not ConfigurationControl.LOCAL
            and added_entities
        ):
            entity_registry = er.async_get(hass)
            for entity_description in (CO2_CALIBRATION, LED_BAR_TEST):
                unique_id = f"{coordinator.serial_number}-{entity_description.key}"
                if entity_id := entity_registry.async_get_entity_id(
                    BUTTON_DOMAIN, DOMAIN, unique_id
                ):
                    entity_registry.async_remove(entity_id)
            added_entities = False