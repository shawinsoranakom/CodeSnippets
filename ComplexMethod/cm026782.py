async def _async_update_data(self) -> dict[int, UptimeRobotMonitor]:
        """Update data."""
        try:
            response = await self.api.async_get_monitors()
        except UptimeRobotAuthenticationException as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except UptimeRobotException as exception:
            raise UpdateFailed(exception) from exception

        if TYPE_CHECKING:
            assert isinstance(response.data, list)

        current_ids = self.data.keys() if self.data else ()
        new_monitors = {monitor.id: monitor for monitor in response.data}
        if stale_ids := set(current_ids) - new_monitors.keys():
            device_registry = dr.async_get(self.hass)

            for monitor_id in stale_ids:
                if device := device_registry.async_get_device(
                    identifiers={(DOMAIN, str(monitor_id))}
                ):
                    device_registry.async_update_device(
                        device_id=device.id,
                        remove_config_entry_id=self.config_entry.entry_id,
                    )

        return new_monitors