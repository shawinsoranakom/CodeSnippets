async def load(self) -> None:
        """Load preferences."""
        stored = await self._store.async_load()
        if stored:
            self._data = AnalyticsData.from_dict(stored)

        if (
            self.supervisor
            and (supervisor_info := hassio.get_supervisor_info(self._hass)) is not None
        ):
            if not self.onboarded:
                # User have not configured analytics, get this setting from the supervisor
                if supervisor_info[ATTR_DIAGNOSTICS] and not self.preferences.get(
                    ATTR_DIAGNOSTICS, False
                ):
                    self._data.preferences[ATTR_DIAGNOSTICS] = True
                elif not supervisor_info[ATTR_DIAGNOSTICS] and self.preferences.get(
                    ATTR_DIAGNOSTICS, False
                ):
                    self._data.preferences[ATTR_DIAGNOSTICS] = False