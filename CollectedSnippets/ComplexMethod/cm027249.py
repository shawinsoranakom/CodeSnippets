def update(
        self, new_data: PassiveBluetoothDataUpdate[_T]
    ) -> set[PassiveBluetoothEntityKey] | None:
        """Update the data and returned changed PassiveBluetoothEntityKey or None on device change.

        The changed PassiveBluetoothEntityKey can be used to filter
        which listeners are called.
        """
        device_change = False
        changed_entity_keys: set[PassiveBluetoothEntityKey] = set()
        for device_key, device_info in new_data.devices.items():
            if device_change or self.devices.get(device_key, UNDEFINED) != device_info:
                device_change = True
                self.devices[device_key] = device_info
        for incoming, current in (
            (new_data.entity_descriptions, self.entity_descriptions),
            (new_data.entity_names, self.entity_names),
            (new_data.entity_data, self.entity_data),
        ):
            for key, data in incoming.items():
                if current.get(key, UNDEFINED) != data:
                    changed_entity_keys.add(key)
                    current[key] = data  # type: ignore[assignment]
        # If the device changed we don't need to return the changed
        # entity keys as all entities will be updated
        return None if device_change else changed_entity_keys