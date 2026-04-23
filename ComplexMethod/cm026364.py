async def async_step_locations(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Handle the user locations and associated usercodes."""
        errors = {}
        if user_input is not None:
            for location_id in self.usercodes:
                if self.usercodes[location_id] is None:
                    valid = await self.hass.async_add_executor_job(
                        self.client.locations[location_id].set_usercode,
                        user_input[CONF_USERCODES],
                    )
                    if valid:
                        self.usercodes[location_id] = user_input[CONF_USERCODES]
                    else:
                        errors[CONF_LOCATION] = "usercode"
                    break

            complete = True
            for location_id in self.usercodes:
                if self.usercodes[location_id] is None:
                    complete = False

            if not errors and complete:
                return self.async_create_entry(
                    title="Total Connect",
                    data={
                        CONF_USERNAME: self.username,
                        CONF_PASSWORD: self.password,
                        CONF_USERCODES: self.usercodes,
                    },
                )
        else:
            if self.client.get_number_locations() < 1:
                return self.async_abort(reason="no_locations")
            for location_id in self.client.locations:
                self.usercodes[location_id] = None

        # show the next location that needs a usercode
        location_codes: VolDictType = {}
        location_for_user = ""
        for location_id in self.usercodes:
            if self.usercodes[location_id] is None:
                location_for_user = str(location_id)
                location_codes[
                    vol.Required(
                        CONF_USERCODES,
                        default="0000",
                    )
                ] = str
                break

        data_schema = vol.Schema(location_codes)
        return self.async_show_form(
            step_id="locations",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"location_id": location_for_user},
        )