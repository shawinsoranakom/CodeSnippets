async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle initial user-triggered config step."""
        hass = self.hass
        schema = create_schema(user_input)

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=schema,
                errors={},
                description_placeholders={},
            )

        host = user_input[CONF_HOST]
        port = user_input[CONF_PORT]

        username = user_input.get(CONF_USERNAME)
        password = user_input.get(CONF_PASSWORD)

        for entry in self._async_current_entries():
            if host == entry.data[CONF_HOST] and port == entry.data[CONF_PORT]:
                return self.async_abort(
                    reason=ADDRESS_ALREADY_CONFIGURED,
                    description_placeholders={"address": f"{host}:{port}"},
                )

        websession = get_maybe_authenticated_session(hass, password, username)

        api_host = ApiHost(
            host, port, DEFAULT_SETUP_TIMEOUT, websession, hass.loop, _LOGGER
        )
        try:
            product = await Box.async_from_host(api_host)

        except UnsupportedBoxVersion as ex:
            return self.handle_step_exception(
                "user",
                ex,
                schema,
                host,
                port,
                UNSUPPORTED_VERSION,
                _LOGGER.debug,
            )
        except UnauthorizedRequest as ex:
            return self.handle_step_exception(
                "user", ex, schema, host, port, CANNOT_CONNECT, _LOGGER.error
            )

        except Error as ex:
            return self.handle_step_exception(
                "user", ex, schema, host, port, CANNOT_CONNECT, _LOGGER.warning
            )

        except RuntimeError as ex:
            return self.handle_step_exception(
                "user", ex, schema, host, port, UNKNOWN, _LOGGER.error
            )

        # Check if configured but IP changed since
        await self.async_set_unique_id(product.unique_id, raise_on_progress=False)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title=product.name, data=user_input)