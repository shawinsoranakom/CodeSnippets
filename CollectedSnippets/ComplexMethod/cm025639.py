async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create an entry for auth."""
        # The default behavior from the parent class is to redirect the
        # user with an external step. When using the device flow, we instead
        # prompt the user to visit a URL and enter a code. The device flow
        # background task will poll the exchange endpoint to get valid
        # creds or until a timeout is complete.
        if self._web_auth:
            return await super().async_step_auth(user_input)

        if self._exchange_finished_task and self._exchange_finished_task.done():
            return self.async_show_progress_done(next_step_id="creation")

        if not self._device_flow:
            _LOGGER.debug("Creating GoogleHybridAuth flow")
            if not isinstance(self.flow_impl, GoogleHybridAuth):
                _LOGGER.error(
                    "Unexpected OAuth implementation does not support device auth: %s",
                    self.flow_impl,
                )
                return self.async_abort(reason="oauth_error")
            calendar_access = DEFAULT_FEATURE_ACCESS
            if self.source == SOURCE_REAUTH and (
                reauth_options := self._get_reauth_entry().options
            ):
                calendar_access = FeatureAccess[reauth_options[CONF_CALENDAR_ACCESS]]
            try:
                device_flow = await async_create_device_flow(
                    self.hass,
                    self.flow_impl.client_id,
                    self.flow_impl.client_secret,
                    calendar_access,
                )
            except TimeoutError as err:
                _LOGGER.error("Timeout initializing device flow: %s", str(err))
                return self.async_abort(reason="timeout_connect")
            except InvalidCredential:
                _LOGGER.debug("Falling back to Web Auth and restarting flow")
                self._web_auth = True
                return await super().async_step_auth()
            except OAuthError as err:
                _LOGGER.error("Error initializing device flow: %s", str(err))
                return self.async_abort(reason="oauth_error")
            self._device_flow = device_flow

            exchange_finished_evt = asyncio.Event()
            self._exchange_finished_task = self.hass.async_create_task(
                exchange_finished_evt.wait()
            )

            def _exchange_finished() -> None:
                self.external_data = {
                    DEVICE_AUTH_CREDS: device_flow.creds
                }  # is None on timeout/expiration
                exchange_finished_evt.set()

            device_flow.async_set_listener(_exchange_finished)
            device_flow.async_start_exchange()

        return self.async_show_progress(
            step_id="auth",
            description_placeholders={
                "url": self._device_flow.verification_url,
                "user_code": self._device_flow.user_code,
            },
            progress_action="exchange",
            progress_task=self._exchange_finished_task,
        )