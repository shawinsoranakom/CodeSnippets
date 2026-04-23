async def _async_update_data(self) -> dict[str, OndiloIcoPoolData]:
        """Fetch pools data from API endpoint and update devices."""
        known_pools: set[str] = set(self.data) if self.data else set()
        try:
            async with UPDATE_LOCK:
                data = await self.hass.async_add_executor_job(self._update_data)
        except OndiloError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        current_pools = set(data)

        new_pools = current_pools - known_pools
        for pool_id in new_pools:
            pool_data = data[pool_id]
            pool_data.measures_coordinator = OndiloIcoMeasuresCoordinator(
                self.hass, self.config_entry, self.api, pool_id
            )
            self._device_registry.async_get_or_create(
                config_entry_id=self.config_entry.entry_id,
                identifiers={(DOMAIN, pool_data.ico["serial_number"])},
                manufacturer="Ondilo",
                model="ICO",
                name=pool_data.pool["name"],
                sw_version=pool_data.ico["sw_version"],
            )

        removed_pools = known_pools - current_pools
        for pool_id in removed_pools:
            pool_data = self.data.pop(pool_id)
            await pool_data.measures_coordinator.async_shutdown()
            device_entry = self._device_registry.async_get_device(
                identifiers={(DOMAIN, pool_data.ico["serial_number"])}
            )
            if device_entry:
                self._device_registry.async_update_device(
                    device_id=device_entry.id,
                    remove_config_entry_id=self.config_entry.entry_id,
                )

        for pool_id in current_pools:
            pool_data = data[pool_id]
            measures_coordinator = pool_data.measures_coordinator
            measures_coordinator.set_next_refresh(pool_data)
            if not measures_coordinator.data:
                await measures_coordinator.async_refresh()

        return data