async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        errors = {}

        if user_input:
            hostname = user_input[CONF_HOSTNAME]
            name = DEFAULT_NAME if hostname == DEFAULT_HOSTNAME else hostname
            resolver = user_input.get(CONF_RESOLVER, DEFAULT_RESOLVER)
            resolver_ipv6 = user_input.get(CONF_RESOLVER_IPV6, DEFAULT_RESOLVER_IPV6)
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            port_ipv6 = user_input.get(CONF_PORT_IPV6, DEFAULT_PORT)

            validate = await async_validate_hostname(
                hostname, resolver, resolver_ipv6, port, port_ipv6
            )

            set_resolver = resolver
            if validate[CONF_IPV6]:
                set_resolver = resolver_ipv6

            if (
                not validate[CONF_IPV4]
                and not validate[CONF_IPV6]
                and not validate[CONF_IPV6_V4]
            ):
                errors["base"] = "invalid_hostname"
            else:
                await self.async_set_unique_id(hostname)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_HOSTNAME: hostname,
                        CONF_NAME: name,
                        CONF_IPV4: validate[CONF_IPV4],
                        CONF_IPV6: validate[CONF_IPV6] or validate[CONF_IPV6_V4],
                    },
                    options={
                        CONF_RESOLVER: resolver,
                        CONF_PORT: port,
                        CONF_RESOLVER_IPV6: set_resolver,
                        CONF_PORT_IPV6: port_ipv6,
                    },
                )

        if self.show_advanced_options is True:
            return self.async_show_form(
                step_id="user",
                data_schema=DATA_SCHEMA_ADV,
                errors=errors,
            )
        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )