def get_zwave_value(
        self,
        value_property: str | int,
        command_class: int | None = None,
        endpoint: int | None = None,
        value_property_key: int | str | None = None,
        add_to_watched_value_ids: bool = True,
        check_all_endpoints: bool = False,
    ) -> ZwaveValue | None:
        """Return specific ZwaveValue on this ZwaveNode."""
        # use commandclass and endpoint from primary value if omitted
        return_value = None
        if command_class is None:
            command_class = self.info.primary_value.command_class
        if endpoint is None:
            endpoint = self.info.primary_value.endpoint

        # lookup value by value_id
        value_id = get_value_id_str(
            self.info.node,
            command_class,
            value_property,
            endpoint=endpoint,
            property_key=value_property_key,
        )
        return_value = self.info.node.values.get(value_id)

        # If we haven't found a value and check_all_endpoints is True, we should
        # return the first value we can find on any other endpoint
        if return_value is None and check_all_endpoints:
            for endpoint_idx in self.info.node.endpoints:
                if endpoint_idx != self.info.primary_value.endpoint:
                    value_id = get_value_id_str(
                        self.info.node,
                        command_class,
                        value_property,
                        endpoint=endpoint_idx,
                        property_key=value_property_key,
                    )
                    return_value = self.info.node.values.get(value_id)
                    if return_value:
                        break

        # add to watched_ids list so we will be triggered when the value updates
        if (
            return_value
            and return_value.value_id not in self.watched_value_ids
            and add_to_watched_value_ids
        ):
            self.watched_value_ids.add(return_value.value_id)
        return return_value