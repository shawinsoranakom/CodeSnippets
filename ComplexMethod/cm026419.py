async def async_step_link(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Attempt to link with the Roomba.

        Given a configured host, will ask the user to press the home and target buttons
        to connect to the device.
        """
        if user_input is None:
            return self.async_show_form(
                step_id="link",
                description_placeholders={CONF_NAME: self.name or self.blid},
            )
        assert self.host
        roomba_pw = RoombaPassword(self.host)

        try:
            password = await self.hass.async_add_executor_job(roomba_pw.get_password)
        except OSError:
            return await self.async_step_link_manual()

        if not password:
            return await self.async_step_link_manual()

        config = {
            CONF_HOST: self.host,
            CONF_BLID: self.blid,
            CONF_PASSWORD: password,
            **DEFAULT_OPTIONS,
        }

        if not self.name:
            try:
                info = await validate_input(self.hass, config)
            except CannotConnect:
                return self.async_abort(reason="cannot_connect")

            self.name = info[CONF_NAME]
        assert self.name
        return self.async_create_entry(title=self.name, data=config)