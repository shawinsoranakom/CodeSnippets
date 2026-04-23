async def async_set_dashboard_info(
        self, addon_slug: str, host: str, port: int
    ) -> None:
        """Set the dashboard info."""
        url = f"http://{host}:{port}"
        hass = self._hass

        if cur_dashboard := self._current_dashboard:
            if cur_dashboard.addon_slug == addon_slug and cur_dashboard.url == url:
                # Do nothing if we already have this data.
                return
            # Clear and make way for new dashboard
            await cur_dashboard.async_shutdown()
            if self._cancel_shutdown is not None:
                self._cancel_shutdown()
                self._cancel_shutdown = None
            self._current_dashboard = None

        dashboard = ESPHomeDashboardCoordinator(hass, addon_slug, url)
        await dashboard.async_request_refresh()

        self._current_dashboard = dashboard

        async def on_hass_stop(_: Event) -> None:
            await dashboard.async_shutdown()

        self._cancel_shutdown = hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, on_hass_stop
        )

        new_data = {"info": {"addon_slug": addon_slug, "host": host, "port": port}}
        if self._data != new_data:
            await self._store.async_save(new_data)

        reloads = [
            hass.config_entries.async_reload(entry.entry_id)
            for entry in hass.config_entries.async_loaded_entries(DOMAIN)
        ]
        # Re-auth flows will check the dashboard for encryption key when the form is requested
        # but we only trigger reauth if the dashboard is available.
        if dashboard.last_update_success:
            reauths = [
                hass.config_entries.flow.async_configure(flow["flow_id"])
                for flow in hass.config_entries.flow.async_progress()
                if flow["handler"] == DOMAIN
                and flow["context"]["source"] == SOURCE_REAUTH
            ]
        else:
            reauths = []
            _LOGGER.error(
                "Dashboard unavailable; skipping reauth: %s", dashboard.last_exception
            )

        _LOGGER.debug(
            "Reloading %d and re-authenticating %d", len(reloads), len(reauths)
        )
        if reloads or reauths:
            await asyncio.gather(*reloads, *reauths)