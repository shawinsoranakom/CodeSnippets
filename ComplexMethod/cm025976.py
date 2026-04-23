async def _async_update_sources(self) -> None:
        """Build source list for entities."""
        self._source_list.clear()
        # Get favorites only if reportedly signed in.
        if self.heos.is_signed_in:
            try:
                self._favorites = await self.heos.get_favorites()
            except HeosError as error:
                _LOGGER.error("Unable to retrieve favorites: %s", error)
            else:
                self._source_list.extend(
                    favorite.name for favorite in self._favorites.values()
                )
        # Get input sources (across all devices in the HEOS system)
        try:
            self._inputs = await self.heos.get_input_sources()
        except HeosError as error:
            _LOGGER.error("Unable to retrieve input sources: %s", error)
        else:
            self._source_list.extend([source.name for source in self._inputs])