async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch data from the Adax."""
        try:
            if hasattr(self.adax_data_handler, "fetch_rooms_info"):
                rooms = await self.adax_data_handler.fetch_rooms_info() or []
                _LOGGER.debug("fetch_rooms_info returned: %s", rooms)
            else:
                _LOGGER.debug("fetch_rooms_info method not available, using get_rooms")
                rooms = []

            if not rooms:
                _LOGGER.debug(
                    "No rooms from fetch_rooms_info, trying get_rooms as fallback"
                )
                rooms = await self.adax_data_handler.get_rooms() or []
                _LOGGER.debug("get_rooms fallback returned: %s", rooms)

            if not rooms:
                raise UpdateFailed("No rooms available from Adax API")

        except OSError as e:
            raise UpdateFailed(f"Error communicating with API: {e}") from e

        for room in rooms:
            room["energyWh"] = int(room.get("energyWh", 0))

        return {r["id"]: r for r in rooms}