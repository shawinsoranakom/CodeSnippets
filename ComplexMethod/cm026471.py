async def async_get_title_data(self, title_id: str, name: str) -> None:
        """Get PS Store Data."""

        app_name = None
        art = None
        media_type = None
        try:
            title = await self._ps4.async_get_ps_store_data(
                name, title_id, self._region
            )

        except PSDataIncomplete:
            title = None
        except TimeoutError:
            title = None
            _LOGGER.error("PS Store Search Timed out")

        else:
            if title is not None:
                app_name = title.name
                art = title.cover_art
                # Assume media type is game if not app.
                if title.game_type != PS_TYPE_APP:
                    media_type = MediaType.GAME
                else:
                    media_type = MediaType.APP
            else:
                _LOGGER.error(
                    "Could not find data in region: %s for PS ID: %s",
                    self._region,
                    title_id,
                )

        finally:
            self._attr_media_title = app_name or name
            self._attr_source = self._attr_media_title
            self._media_image = art or None
            self._attr_media_content_type = media_type

            await self.hass.async_add_executor_job(self.update_list)
            self.async_write_ha_state()