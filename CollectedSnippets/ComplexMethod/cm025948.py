def _async_add_remove_locks(self) -> None:
        """Add new locks, remove non-existing locks."""
        if not self._locks_last_update:
            self._locks_last_update = set(self.tedee_client.locks_dict)

        if (
            current_locks := set(self.tedee_client.locks_dict)
        ) == self._locks_last_update:
            return

        # remove old locks
        if removed_locks := self._locks_last_update - current_locks:
            _LOGGER.debug("Removed locks: %s", ", ".join(map(str, removed_locks)))
            device_registry = dr.async_get(self.hass)
            for lock_id in removed_locks:
                if device := device_registry.async_get_device(
                    identifiers={(DOMAIN, str(lock_id))}
                ):
                    device_registry.async_update_device(
                        device_id=device.id,
                        remove_config_entry_id=self.config_entry.entry_id,
                    )

        # add new locks
        if new_locks := current_locks - self._locks_last_update:
            _LOGGER.debug("New locks found: %s", ", ".join(map(str, new_locks)))
            for callback in self.new_lock_callbacks:
                callback([self.data[lock_id] for lock_id in new_locks])

        self._locks_last_update = current_locks