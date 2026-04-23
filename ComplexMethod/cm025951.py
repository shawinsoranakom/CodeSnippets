async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        is_first_update = not self.data
        client = self.supervisor_client

        try:
            # Cast is required here because asyncio.gather only has overloads to
            # maintain typing for 6 arguments. It falls back to list[<common parent>]
            # after that which is what mypy sees here since we have 7 API calls.
            (
                info,
                core_info,
                supervisor_info,
                os_info,
                host_info,
                store_info,
                network_info,
            ) = cast(
                tuple[
                    RootInfo,
                    HomeAssistantInfo,
                    SupervisorInfo,
                    OSInfo,
                    HostInfo,
                    StoreInfo,
                    NetworkInfo,
                ],
                await asyncio.gather(
                    client.info(),
                    client.homeassistant.info(),
                    client.supervisor.info(),
                    client.os.info(),
                    client.host.info(),
                    client.store.info(),
                    client.network.info(),
                ),
            )
            mounts_info = await client.mounts.info()
            await self.jobs.refresh_data(is_first_update)
        except SupervisorError as err:
            raise UpdateFailed(f"Error on Supervisor API: {err}") from err

        # Build clean coordinator data
        new_data: dict[str, Any] = {}
        new_data[DATA_KEY_CORE] = core_info.to_dict()
        new_data[DATA_KEY_SUPERVISOR] = supervisor_info.to_dict()
        new_data[DATA_KEY_HOST] = host_info.to_dict()
        new_data[DATA_KEY_MOUNTS] = {mount.name: mount for mount in mounts_info.mounts}
        if self.is_hass_os:
            new_data[DATA_KEY_OS] = os_info.to_dict()

        # Update hass.data for legacy accessor functions
        self.hass.data[DATA_INFO] = info
        self.hass.data[DATA_CORE_INFO] = core_info
        self.hass.data[DATA_OS_INFO] = os_info
        self.hass.data[DATA_HOST_INFO] = host_info
        self.hass.data[DATA_STORE] = store_info
        self.hass.data[DATA_NETWORK_INFO] = network_info
        self.hass.data[DATA_SUPERVISOR_INFO] = supervisor_info

        # If this is the initial refresh, register all main components
        if is_first_update:
            async_register_mounts_in_dev_reg(
                self.entry_id, self.dev_reg, new_data[DATA_KEY_MOUNTS].values()
            )
            async_register_core_in_dev_reg(
                self.entry_id, self.dev_reg, new_data[DATA_KEY_CORE]
            )
            async_register_supervisor_in_dev_reg(
                self.entry_id, self.dev_reg, new_data[DATA_KEY_SUPERVISOR]
            )
            async_register_host_in_dev_reg(self.entry_id, self.dev_reg)
            if self.is_hass_os:
                async_register_os_in_dev_reg(
                    self.entry_id, self.dev_reg, new_data[DATA_KEY_OS]
                )

        # Remove mounts that no longer exists from device registry
        supervisor_mount_devices = {
            device.name
            for device in self.dev_reg.devices.get_devices_for_config_entry_id(
                self.entry_id
            )
            if device.model == SupervisorEntityModel.MOUNT
        }
        if stale_mounts := supervisor_mount_devices - set(new_data[DATA_KEY_MOUNTS]):
            async_remove_devices_from_dev_reg(
                self.dev_reg, {f"mount_{stale_mount}" for stale_mount in stale_mounts}
            )

        if not self.is_hass_os and (
            dev := self.dev_reg.async_get_device(identifiers={(DOMAIN, "OS")})
        ):
            # Remove the OS device if it exists and the installation is not hassos
            self.dev_reg.async_remove_device(dev.id)

        # If there are new mounts, we should reload the config entry so we can
        # create new devices and entities. We can return an empty dict because
        # coordinator will be recreated.
        if self.data and (
            set(new_data[DATA_KEY_MOUNTS]) - set(self.data.get(DATA_KEY_MOUNTS, {}))
        ):
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(self.entry_id)
            )
            return {}

        return new_data