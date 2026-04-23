async def async_multicast_set_value(self, service: ServiceCall) -> None:
        """Set a value via multicast to multiple nodes."""
        nodes: set[ZwaveNode] = service.data[const.ATTR_NODES]
        broadcast: bool = service.data[const.ATTR_BROADCAST]
        options = service.data.get(const.ATTR_OPTIONS)

        if not broadcast and len(nodes) == 1:
            _LOGGER.info(
                "Passing the zwave_js.multicast_set_value service call to the "
                "zwave_js.set_value service since only one node was targeted"
            )
            await self.async_set_value(service)
            return

        command_class: CommandClass = service.data[const.ATTR_COMMAND_CLASS]
        property_: int | str = service.data[const.ATTR_PROPERTY]
        property_key: int | str | None = service.data.get(const.ATTR_PROPERTY_KEY)
        endpoint: int | None = service.data.get(const.ATTR_ENDPOINT)

        value = ValueDataType(commandClass=command_class, property=property_)
        if property_key is not None:
            value["propertyKey"] = property_key
        if endpoint is not None:
            value["endpoint"] = endpoint

        new_value = service.data[const.ATTR_VALUE]

        # If there are no nodes, we can assume there is only one config entry due to
        # schema validation and can use that to get the client, otherwise we can just
        # get the client from the node.
        client: ZwaveClient
        first_node: ZwaveNode
        try:
            first_node = next(node for node in nodes)
            client = first_node.client
        except StopIteration:
            data = self._hass.config_entries.async_entries(const.DOMAIN)[0].runtime_data
            client = data.client
            assert client.driver
            first_node = next(
                node
                for node in client.driver.controller.nodes.values()
                if get_value_id_str(
                    node, command_class, property_, endpoint, property_key
                )
                in node.values
            )

        # If value has a string type but the new value is not a string, we need to
        # convert it to one
        value_id = get_value_id_str(
            first_node, command_class, property_, endpoint, property_key
        )
        if (
            value_id in first_node.values
            and first_node.values[value_id].metadata.type == "string"
            and not isinstance(new_value, str)
        ):
            new_value = str(new_value)

        try:
            result = await async_multicast_set_value(
                client=client,
                new_value=new_value,
                value_data=value,
                nodes=None if broadcast else list(nodes),
                options=options,
            )
        except FailedZWaveCommand as err:
            raise HomeAssistantError("Unable to set value via multicast") from err

        if result.status not in SET_VALUE_SUCCESS:
            raise HomeAssistantError(
                "Unable to set value via multicast"
            ) from SetValueFailed(f"{result.status} {result.message}")