def _check_entities() -> None:
        received_outputs = {out.index for out in coordinator.webio_api.outputs}
        added = {i for i in received_outputs if i not in current_outputs}
        removed = {i for i in current_outputs if i not in received_outputs}
        entities_to_add: list[RelaySwitch] = []
        for index in added:
            webio_output = _get_output(coordinator, index)
            if not isinstance(webio_output, NASwebOutput):
                _LOGGER.error("Cannot create RelaySwitch entity without NASwebOutput")
                continue
            new_output = RelaySwitch(coordinator, webio_output)
            entities_to_add.append(new_output)
            current_outputs.add(index)
        async_add_entities(entities_to_add)
        entity_registry = er.async_get(hass)
        for index in removed:
            unique_id = f"{DOMAIN}.{config.unique_id}.relay_switch.{index}"
            if entity_id := entity_registry.async_get_entity_id(
                SWITCH_DOMAIN, DOMAIN, unique_id
            ):
                entity_registry.async_remove(entity_id)
                current_outputs.remove(index)
            else:
                _LOGGER.warning("Failed to remove old output: no entity_id")