async def async_setup_finish(
        self, discovery_integration_import: bool = False
    ) -> ConfigFlowResult:
        """Finish Nanoleaf config flow."""
        try:
            await self.nanoleaf.get_info()
        except Unavailable:
            return self.async_abort(reason="cannot_connect")
        except InvalidToken:
            return self.async_abort(reason="invalid_token")
        except Exception:
            _LOGGER.exception(
                "Unknown error connecting with Nanoleaf at %s", self.nanoleaf.host
            )
            return self.async_abort(reason="unknown")
        name = self.nanoleaf.name

        await self.async_set_unique_id(
            name, raise_on_progress=self.source != SOURCE_USER
        )
        self._abort_if_unique_id_configured({CONF_HOST: self.nanoleaf.host})

        if discovery_integration_import:
            if self.nanoleaf.host in self.discovery_conf:
                self.discovery_conf.pop(self.nanoleaf.host)
            if self.device_id in self.discovery_conf:
                self.discovery_conf.pop(self.device_id)
            _LOGGER.debug(
                "Successfully imported Nanoleaf %s from the discovery integration",
                name,
            )
            if self.discovery_conf:
                await self.hass.async_add_executor_job(
                    save_json, self.hass.config.path(CONFIG_FILE), self.discovery_conf
                )
            else:
                await self.hass.async_add_executor_job(
                    os.remove, self.hass.config.path(CONFIG_FILE)
                )

        return self.async_create_entry(
            title=name,
            data={
                CONF_HOST: self.nanoleaf.host,
                CONF_TOKEN: self.nanoleaf.auth_token,
            },
        )