async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the submitted configuration."""
        errors = {}
        if user_input is not None:
            if await self.hass.async_add_executor_job(self._session.authorize):
                host = self._host or CLOUD_NAME
                if self._host:
                    session = {CONF_HOST: host, KEY_TOKEN: self._session.access_token}
                else:
                    session = {
                        KEY_TOKEN: self._session.access_token,
                        KEY_TOKEN_SECRET: self._session.access_token_secret,
                    }
                return self.async_create_entry(
                    title=host,
                    data={
                        CONF_HOST: host,
                        KEY_SCAN_INTERVAL: self._scan_interval.total_seconds(),
                        KEY_SESSION: session,
                    },
                )
            errors["base"] = "invalid_auth"

        try:
            async with asyncio.timeout(10):
                auth_url = await self.hass.async_add_executor_job(self._get_auth_url)
            if not auth_url:
                return self.async_abort(reason="unknown_authorize_url_generation")
        except TimeoutError:
            return self.async_abort(reason="authorize_url_timeout")
        except Exception:
            _LOGGER.exception("Unexpected error generating auth url")
            return self.async_abort(reason="unknown_authorize_url_generation")

        _LOGGER.debug("Got authorization URL %s", auth_url)
        return self.async_show_form(
            step_id="auth",
            errors=errors,
            description_placeholders={
                "app_name": APPLICATION_NAME,
                "auth_url": auth_url,
            },
        )