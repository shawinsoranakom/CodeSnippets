async def async_step_link(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Prompt user input. Create or edit entry."""
        regions = sorted(COUNTRIES.keys())
        default_region = None
        errors = {}

        if user_input is None:
            # Search for device.
            # If LOCAL_UDP_PORT cannot be used, a random port will be selected.
            devices = await self.hass.async_add_executor_job(
                self.helper.has_devices, self.m_device, LOCAL_UDP_PORT
            )

            # Abort if can't find device.
            if not devices:
                return self.async_abort(reason="no_devices_found")

            self.device_list = [device["host-ip"] for device in devices]

            # Check that devices found aren't configured per account.
            entries = self._async_current_entries()
            if entries:
                # Retrieve device data from all entries if creds match.
                conf_devices = [
                    device
                    for entry in entries
                    if self.creds == entry.data[CONF_TOKEN]
                    for device in entry.data["devices"]
                ]

                # Remove configured device from search list.
                for c_device in conf_devices:
                    if c_device["host"] in self.device_list:
                        # Remove configured device from search list.
                        self.device_list.remove(c_device["host"])

                # If list is empty then all devices are configured.
                if not self.device_list:
                    return self.async_abort(reason="already_configured")

        # Login to PS4 with user data.
        if user_input is not None:
            self.region = user_input[CONF_REGION]
            self.name = user_input[CONF_NAME]
            # Assume pin had leading zeros, before coercing to int.
            self.pin = str(user_input[CONF_CODE]).zfill(PIN_LENGTH)
            self.host = user_input[CONF_IP_ADDRESS]

            is_ready, is_login = await self.hass.async_add_executor_job(
                self.helper.link,
                self.host,
                self.creds,
                self.pin,
                DEFAULT_ALIAS,
                LOCAL_UDP_PORT,
            )

            if is_ready is False:
                errors["base"] = "cannot_connect"
            elif is_login is False:
                errors["base"] = "login_failed"
            else:
                device = {
                    CONF_HOST: self.host,
                    CONF_NAME: self.name,
                    CONF_REGION: self.region,
                }

                # Create entry.
                return self.async_create_entry(
                    title="PlayStation 4",
                    data={CONF_TOKEN: self.creds, "devices": [device]},
                )

        # Try to find region automatically.
        if not self.location:
            self.location = await location_util.async_detect_location_info(
                async_get_clientsession(self.hass)
            )
        if self.location:
            country = COUNTRYCODE_NAMES.get(self.location.country_code)
            if country in COUNTRIES:
                default_region = country

        # Show User Input form.
        link_schema = OrderedDict[vol.Marker, Any]()
        link_schema[vol.Required(CONF_IP_ADDRESS)] = vol.In(list(self.device_list))
        link_schema[vol.Required(CONF_REGION, default=default_region)] = vol.In(
            list(regions)
        )
        link_schema[vol.Required(CONF_CODE)] = vol.All(
            vol.Strip, vol.Length(max=PIN_LENGTH), vol.Coerce(int)
        )
        link_schema[vol.Required(CONF_NAME, default=DEFAULT_NAME)] = str

        return self.async_show_form(
            step_id="link", data_schema=vol.Schema(link_schema), errors=errors
        )