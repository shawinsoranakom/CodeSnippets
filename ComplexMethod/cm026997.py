async def async_set_config_parameter(self, service: ServiceCall) -> None:
        """Set a config value on a node."""
        nodes: set[ZwaveNode] = service.data[const.ATTR_NODES]
        endpoint = service.data[const.ATTR_ENDPOINT]
        property_or_property_name = service.data[const.ATTR_CONFIG_PARAMETER]
        property_key = service.data.get(const.ATTR_CONFIG_PARAMETER_BITMASK)
        new_value = service.data[const.ATTR_CONFIG_VALUE]
        value_size = service.data.get(const.ATTR_VALUE_SIZE)
        value_format = service.data.get(const.ATTR_VALUE_FORMAT)

        nodes_without_endpoints: set[ZwaveNode] = set()
        # Remove nodes that don't have the specified endpoint
        for node in nodes:
            if endpoint not in node.endpoints:
                nodes_without_endpoints.add(node)
        nodes = nodes.difference(nodes_without_endpoints)
        if not nodes:
            raise HomeAssistantError(
                "None of the specified nodes have the specified endpoint"
            )
        if nodes_without_endpoints and _LOGGER.isEnabledFor(logging.WARNING):
            _LOGGER.warning(
                "The following nodes do not have endpoint %x and will be skipped: %s",
                endpoint,
                nodes_without_endpoints,
            )

        # If value_size isn't provided, we will use the utility function which includes
        # additional checks and protections. If it is provided, we will use the
        # node.async_set_raw_config_parameter_value method which calls the
        # Configuration CC set API.
        results = await asyncio.gather(
            *(
                async_set_config_parameter(
                    node,
                    new_value,
                    property_or_property_name,
                    property_key=property_key,
                    endpoint=endpoint,
                )
                if value_size is None
                else node.endpoints[endpoint].async_set_raw_config_parameter_value(
                    new_value,
                    property_or_property_name,
                    property_key=property_key,
                    value_size=value_size,
                    value_format=value_format,
                )
                for node in nodes
            ),
            return_exceptions=True,
        )

        def process_results(
            nodes_or_endpoints_list: Sequence[_NodeOrEndpointType], _results: list[Any]
        ) -> None:
            """Process results for given nodes or endpoints."""
            for node_or_endpoint, result in get_valid_responses_from_results(
                nodes_or_endpoints_list, _results
            ):
                if value_size is None:
                    # async_set_config_parameter still returns (Value, SetConfigParameterResult)
                    zwave_value = result[0]
                    cmd_status = result[1]
                else:
                    # async_set_raw_config_parameter_value now returns just SetConfigParameterResult
                    cmd_status = result
                    zwave_value = f"parameter {property_or_property_name}"

                if cmd_status.status == CommandStatus.ACCEPTED:
                    msg = "Set configuration parameter %s on Node %s with value %s"
                else:
                    msg = (
                        "Added command to queue to set configuration parameter %s on %s "
                        "with value %s. Parameter will be set when the device wakes up"
                    )
                _LOGGER.info(msg, zwave_value, node_or_endpoint, new_value)
            raise_exceptions_from_results(nodes_or_endpoints_list, _results)

        if value_size is None:
            process_results(list(nodes), results)
        else:
            process_results([node.endpoints[endpoint] for node in nodes], results)