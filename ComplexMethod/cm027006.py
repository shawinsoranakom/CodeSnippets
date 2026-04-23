def async_on_value_updated(
        value: Value, device: dr.DeviceEntry, event: dict
    ) -> None:
        """Handle value update."""
        event_value: Value = event["value"]
        if event_value != value:
            return

        # Get previous value and its state value if it exists
        prev_value_raw = event["args"]["prevValue"]
        prev_value = value.metadata.states.get(str(prev_value_raw), prev_value_raw)
        # Get current value and its state value if it exists
        curr_value_raw = event["args"]["newValue"]
        curr_value = value.metadata.states.get(str(curr_value_raw), curr_value_raw)
        # Check from and to values against previous and current values respectively
        for value_to_eval, raw_value_to_eval, match in (
            (prev_value, prev_value_raw, from_value),
            (curr_value, curr_value_raw, to_value),
        ):
            if match not in (MATCH_ALL, value_to_eval, raw_value_to_eval) and not (
                isinstance(match, list)
                and (value_to_eval in match or raw_value_to_eval in match)
            ):
                return

        device_name = device.name_by_user or device.name
        description = f"Z-Wave value {value.value_id} updated on {device_name}"
        payload = {
            ATTR_DEVICE_ID: device.id,
            ATTR_NODE_ID: value.node.node_id,
            ATTR_COMMAND_CLASS: value.command_class,
            ATTR_COMMAND_CLASS_NAME: value.command_class_name,
            ATTR_PROPERTY: value.property_,
            ATTR_PROPERTY_NAME: value.property_name,
            ATTR_ENDPOINT: endpoint,
            ATTR_PROPERTY_KEY: value.property_key,
            ATTR_PROPERTY_KEY_NAME: value.property_key_name,
            ATTR_PREVIOUS_VALUE: prev_value,
            ATTR_PREVIOUS_VALUE_RAW: prev_value_raw,
            ATTR_CURRENT_VALUE: curr_value,
            ATTR_CURRENT_VALUE_RAW: curr_value_raw,
        }

        run_action(payload, description)