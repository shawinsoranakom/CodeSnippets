async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Store current values in case setup fails and user needs to edit
            self._user_schema = _get_config_schema(user_input)
            if self.unique_id is None:
                unique_id = await VizioAsync.get_unique_id(
                    user_input[CONF_HOST],
                    user_input[CONF_DEVICE_CLASS],
                    session=async_get_clientsession(self.hass, False),
                )

                # Check if unique ID was found, set unique ID, and abort if a flow with
                # the same unique ID is already in progress
                if not unique_id:
                    errors[CONF_HOST] = "cannot_connect"
                elif (
                    await self.async_set_unique_id(
                        unique_id=unique_id, raise_on_progress=True
                    )
                    is not None
                ):
                    errors[CONF_HOST] = "existing_config_entry_found"

            if not errors:
                if self._must_show_form and self.context["source"] == SOURCE_ZEROCONF:
                    # Discovery should always display the config form before trying to
                    # create entry so that user can update default config options
                    self._must_show_form = False
                elif user_input[
                    CONF_DEVICE_CLASS
                ] == MediaPlayerDeviceClass.SPEAKER or user_input.get(
                    CONF_ACCESS_TOKEN
                ):
                    # Ensure config is valid for a device
                    if not await VizioAsync.validate_ha_config(
                        user_input[CONF_HOST],
                        user_input.get(CONF_ACCESS_TOKEN),
                        user_input[CONF_DEVICE_CLASS],
                        session=async_get_clientsession(self.hass, False),
                    ):
                        errors["base"] = "cannot_connect"

                    if not errors:
                        return await self._create_entry(user_input)
                else:
                    self._data = copy.deepcopy(user_input)
                    return await self.async_step_pair_tv()

        schema = self._user_schema or _get_config_schema()
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)