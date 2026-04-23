def _async_on_event(
        self, event_data: dict, device: dr.DeviceEntry | None = None
    ) -> None:
        """Handle event."""
        for key, val in self._event_data_filter.items():
            if key not in event_data:
                return
            if (
                self._options[ATTR_PARTIAL_DICT_MATCH]
                and isinstance(event_data[key], dict)
                and isinstance(val, dict)
            ):
                for key2, val2 in val.items():
                    if key2 not in event_data[key] or event_data[key][key2] != val2:
                        return
                continue
            if event_data[key] != val:
                return

        payload: dict[str, Any] = {
            ATTR_EVENT_SOURCE: self._event_source,
            ATTR_EVENT: self._event_name,
            ATTR_EVENT_DATA: event_data,
        }

        primary_desc = (
            f"Z-Wave JS '{self._event_source}' event '{self._event_name}' was emitted"
        )

        description = primary_desc
        if device:
            device_name = device.name_by_user or device.name
            payload[ATTR_DEVICE_ID] = device.id
            home_and_node_id = get_home_and_node_id_from_device_entry(device)
            assert home_and_node_id
            payload[ATTR_NODE_ID] = home_and_node_id[1]
            description = f"{primary_desc} on {device_name}"

        description = f"{description} with event data: {event_data}"
        self._action_runner(payload, description)