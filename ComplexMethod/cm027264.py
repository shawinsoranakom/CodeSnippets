async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle users reauth credentials."""

        if self.tado is None:
            _LOGGER.debug("Initiating device activation")
            try:
                self.tado = await self.hass.async_add_executor_job(Tado)
            except TadoException:
                _LOGGER.exception("Error while initiating Tado")
                return self.async_abort(reason="cannot_connect")
            assert self.tado is not None
            tado_device_url = self.tado.device_verification_url()
            user_code = URL(tado_device_url).query["user_code"]

        async def _wait_for_login() -> None:
            """Wait for the user to login."""
            assert self.tado is not None
            _LOGGER.debug("Waiting for device activation")
            try:
                await self.hass.async_add_executor_job(self.tado.device_activation)
            except Exception as ex:
                ratelimit = await self.hass.async_add_executor_job(
                    self.tado.rate_limit_info
                )
                if ratelimit.get("remaining") == "0":
                    _LOGGER.error(
                        "Tado API rate limit reached while waiting for device activation: %s",
                        ex,
                    )
                    raise TadoRateLimitExceeded from ex
                _LOGGER.exception("Error while waiting for device activation")
                raise CannotConnect from ex

            if (
                self.tado.device_activation_status()
                is not DeviceActivationStatus.COMPLETED
            ):
                raise CannotConnect

        _LOGGER.debug("Checking login task")
        if self.login_task is None:
            _LOGGER.debug("Creating task for device activation")
            self.login_task = self.hass.async_create_task(_wait_for_login())

        if self.login_task.done():
            _LOGGER.debug("Login task is done, checking results")
            ex = self.login_task.exception()
            if isinstance(ex, TadoRateLimitExceeded):
                return self.async_abort(reason="api_rate_limit_reached")
            if ex:
                return self.async_show_progress_done(next_step_id="timeout")
            self.refresh_token = await self.hass.async_add_executor_job(
                self.tado.get_refresh_token
            )
            return self.async_show_progress_done(next_step_id="finish_login")

        return self.async_show_progress(
            step_id="user",
            progress_action="wait_for_device",
            description_placeholders={
                "url": tado_device_url,
                "code": user_code,
            },
            progress_task=self.login_task,
        )