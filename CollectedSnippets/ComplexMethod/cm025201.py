async def _async_update_data(self) -> None:
        """Update all device states from the Litter-Robot API."""
        try:
            await self.account.load_robots(subscribe_for_updates=True)
            await self.account.load_pets()
            for pet in self.account.pets:
                # Need to fetch weight history for `get_visits_since`
                await pet.fetch_weight_history()
        except LitterRobotLoginException as ex:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="invalid_credentials"
            ) from ex
        except LitterRobotException as ex:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
                translation_placeholders={"error": str(ex)},
            ) from ex

        current_members = {robot.serial for robot in self.account.robots} | {
            pet.id for pet in self.account.pets
        }
        if stale_members := self.previous_members - current_members:
            device_registry = dr.async_get(self.hass)
            for device_id in stale_members:
                device = device_registry.async_get_device(
                    identifiers={(DOMAIN, device_id)}
                )
                if device:
                    device_registry.async_update_device(
                        device_id=device.id,
                        remove_config_entry_id=self.config_entry.entry_id,
                    )
        self.previous_members = current_members