async def async_step_device(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle device steps."""

        async def _wait_for_login() -> None:
            if TYPE_CHECKING:
                # mypy is not aware that we can't get here without having these set already
                assert self._device is not None
                assert self._login_device is not None

            response = await self._device.activation(
                device_code=self._login_device.device_code
            )
            self._login = response.data

        if not self._device:
            self._device = GitHubDeviceAPI(
                client_id=CLIENT_ID,
                session=async_get_clientsession(self.hass),
                client_name=SERVER_SOFTWARE,
            )

            try:
                response = await self._device.register()
                self._login_device = response.data
            except GitHubException as exception:
                LOGGER.exception(exception)
                return self.async_abort(reason="could_not_register")

        if self.login_task is None:
            self.login_task = self.hass.async_create_task(_wait_for_login())

        if self.login_task.done():
            if self.login_task.exception():
                return self.async_show_progress_done(next_step_id="could_not_register")
            return self.async_show_progress_done(next_step_id="repositories")

        if TYPE_CHECKING:
            # mypy is not aware that we can't get here without having this set already
            assert self._login_device is not None

        return self.async_show_progress(
            step_id="device",
            progress_action="wait_for_device",
            description_placeholders={
                "url": OAUTH_USER_LOGIN,
                "code": self._login_device.user_code,
            },
            progress_task=self.login_task,
        )