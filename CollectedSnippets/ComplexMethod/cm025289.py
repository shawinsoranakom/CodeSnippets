def _add_remove_locks(self) -> None:
        """Add newly discovered locks and remove nonexistent locks."""
        device_registry = dr.async_get(self.hass)
        devices = dr.async_entries_for_config_entry(
            device_registry, self.config_entry.entry_id
        )
        previous_locks = set()
        previous_locks_by_lock_id = {}
        for device in devices:
            for domain, identifier in device.identifiers:
                if domain == DOMAIN:
                    previous_locks.add(identifier)
                    previous_locks_by_lock_id[identifier] = device
                    continue
        current_locks = set(self.data.locks.keys())

        if removed_locks := previous_locks - current_locks:
            LOGGER.debug("Removed locks: %s", ", ".join(removed_locks))
            for lock_id in removed_locks:
                device_registry.async_update_device(
                    device_id=previous_locks_by_lock_id[lock_id].id,
                    remove_config_entry_id=self.config_entry.entry_id,
                )

        if new_lock_ids := current_locks - previous_locks:
            LOGGER.debug("New locks found: %s", ", ".join(new_lock_ids))
            new_locks = {lock_id: self.data.locks[lock_id] for lock_id in new_lock_ids}
            for new_lock_callback in self.new_locks_callbacks:
                new_lock_callback(new_locks)