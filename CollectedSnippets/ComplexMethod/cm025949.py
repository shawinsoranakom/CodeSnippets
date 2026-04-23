async def _fetch_stats(self) -> None:
        """Fetch container stats for subscribed entities."""
        container_updates = self._container_updates
        data = self.hass.data
        client = self.supervisor_client

        # Fetch core and supervisor stats
        updates: dict[str, Awaitable] = {}
        if container_updates.get(CORE_CONTAINER, {}).get(CONTAINER_STATS):
            updates[DATA_CORE_STATS] = client.homeassistant.stats()
        if container_updates.get(SUPERVISOR_CONTAINER, {}).get(CONTAINER_STATS):
            updates[DATA_SUPERVISOR_STATS] = client.supervisor.stats()

        if updates:
            api_results: list[ResponseData] = await asyncio.gather(*updates.values())
            for key, result in zip(updates, api_results, strict=True):
                data[key] = result.to_dict()

        # Fetch addon stats
        addons_list: list[InstalledAddon] = self.hass.data.get(DATA_ADDONS_LIST) or []
        started_addons = {
            addon.slug
            for addon in addons_list
            if addon.state in {AddonState.STARTED, AddonState.STARTUP}
        }

        addons_stats: dict[str, Any] = data.setdefault(DATA_ADDONS_STATS, {})

        # Clean up cache for stopped/removed addons
        for slug in addons_stats.keys() - started_addons:
            del addons_stats[slug]

        # Fetch stats for addons with subscribed entities
        addon_stats_results = dict(
            await asyncio.gather(
                *[
                    self._update_addon_stats(slug)
                    for slug in started_addons
                    if container_updates.get(slug, {}).get(CONTAINER_STATS)
                ]
            )
        )
        addons_stats.update(addon_stats_results)