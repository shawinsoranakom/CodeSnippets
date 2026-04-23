async def _update_app_list(self) -> None:
        _LOGGER.debug("Updating app list")
        if not self.atv:
            return
        try:
            apps = await self.atv.apps.app_list()
        except exceptions.NotSupportedError:
            _LOGGER.error("Listing apps is not supported")
        except exceptions.ProtocolError:
            _LOGGER.exception("Failed to update app list")
        else:
            self._app_list = {
                app_name: app.identifier
                for app in sorted(apps, key=lambda app: (app.name or "").lower())
                if (app_name := app.name) is not None
            }
            self.async_write_ha_state()