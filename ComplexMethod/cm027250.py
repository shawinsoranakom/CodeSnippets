def async_update_listeners(
        self,
        data: PassiveBluetoothDataUpdate[_T] | None,
        was_available: bool | None = None,
        changed_entity_keys: set[PassiveBluetoothEntityKey] | None = None,
    ) -> None:
        """Update all registered listeners."""
        if was_available is None:
            was_available = self.coordinator.available

        # Dispatch to listeners without a filter key
        for update_callback in self._listeners:
            update_callback(data)

        if not was_available or data is None:
            # When data is None, or was_available is False,
            # dispatch to all listeners as it means the device
            # is flipping between available and unavailable
            for listeners in self._entity_key_listeners.values():
                for update_callback in listeners:
                    update_callback(data)
            return

        # Dispatch to listeners with a filter key
        # if the key is in the data
        entity_key_listeners = self._entity_key_listeners
        for entity_key in data.entity_data:
            if (
                was_available
                and changed_entity_keys is not None
                and entity_key not in changed_entity_keys
            ):
                continue
            if maybe_listener := entity_key_listeners.get(entity_key):
                for update_callback in maybe_listener:
                    update_callback(data)