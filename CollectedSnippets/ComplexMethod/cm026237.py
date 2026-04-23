async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Reconfigure Telegram bot."""

        api_key: str = self._get_reconfigure_entry().data[CONF_API_KEY]
        await self.async_set_unique_id(api_key)
        self._abort_if_unique_id_mismatch()

        if not user_input:
            return self.async_show_form(
                step_id="reconfigure",
                data_schema=self.add_suggested_values_to_schema(
                    STEP_RECONFIGURE_USER_DATA_SCHEMA,
                    {
                        **self._get_reconfigure_entry().data,
                        SECTION_ADVANCED_SETTINGS: {
                            CONF_API_ENDPOINT: self._get_reconfigure_entry().data[
                                CONF_API_ENDPOINT
                            ],
                            CONF_PROXY_URL: self._get_reconfigure_entry().data.get(
                                CONF_PROXY_URL
                            ),
                        },
                    },
                ),
                description_placeholders=DESCRIPTION_PLACEHOLDERS,
            )
        user_input[CONF_PROXY_URL] = user_input[SECTION_ADVANCED_SETTINGS].get(
            CONF_PROXY_URL
        )

        user_input[CONF_API_ENDPOINT] = user_input[SECTION_ADVANCED_SETTINGS][
            CONF_API_ENDPOINT
        ]

        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = DESCRIPTION_PLACEHOLDERS.copy()

        user_input[CONF_API_KEY] = api_key
        bot_name = await self._validate_bot(
            user_input, errors, description_placeholders
        )
        self._bot_name = bot_name

        existing_api_endpoint: str = self._get_reconfigure_entry().data[
            CONF_API_ENDPOINT
        ]
        if (
            self._get_reconfigure_entry().state == ConfigEntryState.LOADED
            and user_input[CONF_API_ENDPOINT] != DEFAULT_API_ENDPOINT
            and existing_api_endpoint == DEFAULT_API_ENDPOINT
        ):
            # logout existing bot from the official Telegram bot API
            # logout is only used when changing the API endpoint from official to a custom one
            # there is a 10-minute lockout period after logout so we only logout if necessary
            service: TelegramNotificationService = (
                self._get_reconfigure_entry().runtime_data
            )
            try:
                is_logged_out = await service.bot.log_out()
            except TelegramError as err:
                errors["base"] = "telegram_error"
                description_placeholders[ERROR_MESSAGE] = str(err)
            else:
                _LOGGER.info(
                    "[%s %s] Logged out: %s",
                    service.bot.username,
                    service.bot.id,
                    is_logged_out,
                )
                if not is_logged_out:
                    errors["base"] = "bot_logout_failed"

        if errors:
            return self.async_show_form(
                step_id="reconfigure",
                data_schema=self.add_suggested_values_to_schema(
                    STEP_RECONFIGURE_USER_DATA_SCHEMA,
                    {
                        **user_input,
                        SECTION_ADVANCED_SETTINGS: {
                            CONF_API_ENDPOINT: user_input[CONF_API_ENDPOINT],
                            CONF_PROXY_URL: user_input.get(CONF_PROXY_URL),
                        },
                    },
                ),
                errors=errors,
                description_placeholders=description_placeholders,
            )

        if user_input[CONF_PLATFORM] != PLATFORM_WEBHOOKS:
            await self._shutdown_bot()

            return self.async_update_and_abort(
                self._get_reconfigure_entry(), title=bot_name, data_updates=user_input
            )

        self._step_user_data.update(user_input)
        return await self.async_step_webhooks()