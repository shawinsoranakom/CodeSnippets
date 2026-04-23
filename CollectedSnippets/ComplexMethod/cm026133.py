async def async_step_reconfigure_v1(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of InfluxDB v1."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            url = URL(user_input[CONF_URL])
            data = {
                CONF_API_VERSION: DEFAULT_API_VERSION,
                CONF_HOST: url.host,
                CONF_PORT: url.port,
                CONF_USERNAME: user_input.get(CONF_USERNAME),
                CONF_PASSWORD: user_input.get(CONF_PASSWORD),
                CONF_DB_NAME: user_input[CONF_DB_NAME],
                CONF_SSL: url.scheme == "https",
                CONF_PATH: url.path,
                CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
            }
            if (cert := user_input.get(CONF_SSL_CA_CERT)) is not None:
                path = await _save_uploaded_cert_file(self.hass, cert)
                data[CONF_SSL_CA_CERT] = str(path)
            elif CONF_SSL_CA_CERT in entry.data:
                data[CONF_SSL_CA_CERT] = entry.data[CONF_SSL_CA_CERT]
            errors = await _validate_influxdb_connection(self.hass, data)

            if not errors:
                title = f"{data[CONF_DB_NAME]} ({data[CONF_HOST]})"
                return self.async_update_reload_and_abort(
                    entry, title=title, data_updates=data
                )

        suggested_values = dict(entry.data) | (user_input or {})
        if user_input is None:
            suggested_values[CONF_URL] = str(
                URL.build(
                    scheme="https" if entry.data.get(CONF_SSL) else "http",
                    host=entry.data.get(CONF_HOST, ""),
                    port=entry.data.get(CONF_PORT),
                    path=entry.data.get(CONF_PATH, ""),
                )
            )

        return self.async_show_form(
            step_id="reconfigure_v1",
            data_schema=self.add_suggested_values_to_schema(
                INFLUXDB_V1_SCHEMA, suggested_values
            ),
            errors=errors,
        )