async def async_invoke_cc_api(self, service: ServiceCall) -> None:
        """Invoke a command class API."""
        command_class: CommandClass = service.data[const.ATTR_COMMAND_CLASS]
        method_name: str = service.data[const.ATTR_METHOD_NAME]
        parameters: list[Any] = service.data[const.ATTR_PARAMETERS]

        # If an endpoint is provided, we assume the user wants to call the CC API on
        # that endpoint for all target nodes
        if (endpoint := service.data.get(const.ATTR_ENDPOINT)) is not None:
            await _async_invoke_cc_api(
                {node.endpoints[endpoint] for node in service.data[const.ATTR_NODES]},
                command_class,
                method_name,
                *parameters,
            )
            return

        # If no endpoint is provided, we target endpoint 0 for all device and area
        # nodes and we target the endpoint of the primary value for all entities
        # specified.
        endpoints: set[Endpoint] = set()
        for area_id in service.data.get(ATTR_AREA_ID, []):
            for node in async_get_nodes_from_area_id(
                self._hass, area_id, self._ent_reg, self._dev_reg
            ):
                endpoints.add(node.endpoints[0])

        for device_id in service.data.get(ATTR_DEVICE_ID, []):
            try:
                node = async_get_node_from_device_id(
                    self._hass, device_id, self._dev_reg
                )
            except ValueError as err:
                _LOGGER.warning(err.args[0])
                continue
            endpoints.add(node.endpoints[0])

        for entity_id in service.data.get(ATTR_ENTITY_ID, []):
            if (
                not (entity_entry := self._ent_reg.async_get(entity_id))
                or entity_entry.platform != const.DOMAIN
            ):
                _LOGGER.warning(
                    "Skipping entity %s as it is not a valid %s entity",
                    entity_id,
                    const.DOMAIN,
                )
                continue
            node = async_get_node_from_entity_id(
                self._hass, entity_id, self._ent_reg, self._dev_reg
            )
            if (
                value_id := get_value_id_from_unique_id(entity_entry.unique_id)
            ) is None:
                _LOGGER.warning("Skipping entity %s as it has no value ID", entity_id)
                continue

            endpoint_idx = node.values[value_id].endpoint
            endpoints.add(
                node.endpoints[endpoint_idx if endpoint_idx is not None else 0]
            )

        await _async_invoke_cc_api(endpoints, command_class, method_name, *parameters)