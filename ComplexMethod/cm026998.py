async def async_set_value(self, service: ServiceCall) -> None:
        """Set a value on a node."""
        nodes: set[ZwaveNode] = service.data[const.ATTR_NODES]
        command_class: CommandClass = service.data[const.ATTR_COMMAND_CLASS]
        property_: int | str = service.data[const.ATTR_PROPERTY]
        property_key: int | str | None = service.data.get(const.ATTR_PROPERTY_KEY)
        endpoint: int | None = service.data.get(const.ATTR_ENDPOINT)
        new_value = service.data[const.ATTR_VALUE]
        wait_for_result = service.data.get(const.ATTR_WAIT_FOR_RESULT)
        options = service.data.get(const.ATTR_OPTIONS)

        coros = []
        for node in nodes:
            value_id = get_value_id_str(
                node,
                command_class,
                property_,
                endpoint=endpoint,
                property_key=property_key,
            )
            # If value has a string type but the new value is not a string, we need to
            # convert it to one. We use new variable `new_value_` to convert the data
            # so we can preserve the original `new_value` for every node.
            if (
                value_id in node.values
                and node.values[value_id].metadata.type == "string"
                and not isinstance(new_value, str)
            ):
                new_value_ = str(new_value)
            else:
                new_value_ = new_value
            coros.append(
                node.async_set_value(
                    value_id,
                    new_value_,
                    options=options,
                    wait_for_result=wait_for_result,
                )
            )

        results = await asyncio.gather(*coros, return_exceptions=True)
        nodes_list = list(nodes)
        # multiple set_values my fail so we will track the entire list
        set_value_failed_nodes_list: list[ZwaveNode] = []
        set_value_failed_error_list: list[SetValueFailed] = []
        for node_, result in get_valid_responses_from_results(nodes_list, results):
            if result and result.status not in SET_VALUE_SUCCESS:
                # If we failed to set a value, add node to exception list
                set_value_failed_nodes_list.append(node_)
                set_value_failed_error_list.append(
                    SetValueFailed(f"{result.status} {result.message}")
                )

        # Add the exception to the results and the nodes to the node list. No-op if
        # no set value commands failed
        raise_exceptions_from_results(
            (*nodes_list, *set_value_failed_nodes_list),
            (*results, *set_value_failed_error_list),
        )