async def async_step_local(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Handle local flow."""
        if user_input is None:
            return self.async_show_form(
                step_id="local",
                data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
                errors={},
            )
        # In a LOCAL setup we still need to resolve the host to serial number
        ip_address = user_input["host"]
        serial_number = None

        # Attempt 1: try to use the local api (older generation) to resolve host to serialnumber
        smappee_api = api.api.SmappeeLocalApi(ip=ip_address)
        logon = await self.hass.async_add_executor_job(smappee_api.logon)
        if logon is not None:
            advanced_config = await self.hass.async_add_executor_job(
                smappee_api.load_advanced_config
            )
            for config_item in advanced_config:
                if config_item["key"] == "mdnsHostName":
                    serial_number = config_item["value"]
        else:
            # Attempt 2: try to use the local mqtt broker (newer generation) to resolve host to serialnumber
            smappee_mqtt = mqtt.SmappeeLocalMqtt()
            connect = await self.hass.async_add_executor_job(smappee_mqtt.start_attempt)
            if not connect:
                return self.async_abort(reason="cannot_connect")

            serial_number = await self.hass.async_add_executor_job(
                smappee_mqtt.start_and_wait_for_config
            )
            await self.hass.async_add_executor_job(smappee_mqtt.stop)
            if serial_number is None:
                return self.async_abort(reason="cannot_connect")

        if serial_number is None or not serial_number.startswith(
            SUPPORTED_LOCAL_DEVICES
        ):
            return self.async_abort(reason="invalid_mdns")

        serial_number = serial_number.replace("Smappee", "")

        # Check if already configured (local)
        await self.async_set_unique_id(serial_number, raise_on_progress=False)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"{DOMAIN}{serial_number}",
            data={CONF_IP_ADDRESS: ip_address, CONF_SERIALNUMBER: serial_number},
        )