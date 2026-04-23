async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        is_first_update = not self.data
        client = self.supervisor_client

        try:
            installed_addons: list[InstalledAddon] = await client.addons.list()
            all_addons = {addon.slug for addon in installed_addons}

            # Fetch addon info for all addons on first update, or only
            # for addons with subscribed entities on subsequent updates.
            addon_info_results = dict(
                await asyncio.gather(
                    *[
                        self._update_addon_info(slug)
                        for slug in all_addons
                        if is_first_update or self._addon_info_subscriptions.get(slug)
                    ]
                )
            )
        except SupervisorError as err:
            raise UpdateFailed(f"Error on Supervisor API: {err}") from err

        # Update hass.data for legacy accessor functions
        self.hass.data[DATA_ADDONS_LIST] = installed_addons

        # Update addon info cache in hass.data
        addon_info_cache: dict[str, Any] = self.hass.data.setdefault(
            DATA_ADDONS_INFO, {}
        )
        for slug in addon_info_cache.keys() - all_addons:
            del addon_info_cache[slug]
        addon_info_cache.update(addon_info_results)

        # Build clean coordinator data
        store = self.hass.data.get(DATA_STORE)
        if store:
            repositories = {repo.slug: repo.name for repo in store.repositories}
        else:
            repositories = {}

        addons_list_dicts = [addon.to_dict() for addon in installed_addons]
        new_data: dict[str, Any] = {}
        new_data[DATA_KEY_ADDONS] = {
            (slug := addon[ATTR_SLUG]): {
                **addon,
                ATTR_AUTO_UPDATE: (addon_info_cache.get(slug) or {}).get(
                    ATTR_AUTO_UPDATE, False
                ),
                ATTR_REPOSITORY: repositories.get(
                    repo_slug := addon.get(ATTR_REPOSITORY, ""), repo_slug
                ),
            }
            for addon in addons_list_dicts
        }

        # If this is the initial refresh, register all addons
        if is_first_update:
            async_register_addons_in_dev_reg(
                self.entry_id, self.dev_reg, new_data[DATA_KEY_ADDONS].values()
            )

        # Remove add-ons that are no longer installed from device registry
        supervisor_addon_devices = {
            list(device.identifiers)[0][1]
            for device in self.dev_reg.devices.get_devices_for_config_entry_id(
                self.entry_id
            )
            if device.model == SupervisorEntityModel.ADDON
        }
        if stale_addons := supervisor_addon_devices - set(new_data[DATA_KEY_ADDONS]):
            async_remove_devices_from_dev_reg(self.dev_reg, stale_addons)

        # If there are new add-ons, we should reload the config entry so we can
        # create new devices and entities. We can return an empty dict because
        # coordinator will be recreated.
        if self.data and (
            set(new_data[DATA_KEY_ADDONS]) - set(self.data[DATA_KEY_ADDONS])
        ):
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(self.entry_id)
            )
            return {}

        return new_data