def _check_entities() -> None:
        received_inputs: dict[int, NASwebInput] = {
            entry.index: entry for entry in coordinator.webio_api.inputs
        }
        added = {i for i in received_inputs if i not in current_inputs}
        removed = {i for i in current_inputs if i not in received_inputs}
        entities_to_add: list[InputStateSensor] = []
        for index in added:
            webio_input = received_inputs[index]
            if not isinstance(webio_input, NASwebInput):
                _LOGGER.error("Cannot create InputStateSensor without NASwebInput")
                continue
            new_input = InputStateSensor(coordinator, webio_input)
            entities_to_add.append(new_input)
            current_inputs.add(index)
        async_add_entities(entities_to_add)
        entity_registry = er.async_get(hass)
        for index in removed:
            unique_id = f"{DOMAIN}.{config.unique_id}.input.{index}"
            if entity_id := entity_registry.async_get_entity_id(
                SENSOR_DOMAIN, DOMAIN, unique_id
            ):
                entity_registry.async_remove(entity_id)
                current_inputs.remove(index)
            else:
                _LOGGER.warning("Failed to remove old input: no entity_id")