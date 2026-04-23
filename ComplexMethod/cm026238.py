async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Create allowed chat ID."""

        if self._get_entry().state != ConfigEntryState.LOADED:
            return self.async_abort(
                reason="entry_not_loaded",
                description_placeholders={"telegram_bot": self._get_entry().title},
            )

        errors: dict[str, str] = {}
        description_placeholders = DESCRIPTION_PLACEHOLDERS.copy()

        if user_input is not None:
            config_entry: TelegramBotConfigEntry = self._get_entry()
            bot = config_entry.runtime_data.bot

            # validate chat id
            chat_id: int = user_input[CONF_CHAT_ID]
            try:
                chat_info: ChatFullInfo = await bot.get_chat(chat_id)
            except BadRequest:
                errors["base"] = "chat_not_found"
            except TelegramError as err:
                errors["base"] = "telegram_error"
                description_placeholders[ERROR_MESSAGE] = str(err)

            if not errors:
                return self.async_create_entry(
                    title=chat_info.effective_name or str(chat_id),
                    data={CONF_CHAT_ID: chat_id},
                    unique_id=str(chat_id),
                )

        service: TelegramNotificationService = self._get_entry().runtime_data
        description_placeholders["bot_username"] = f"@{service.bot.username}"
        description_placeholders["bot_url"] = f"https://t.me/{service.bot.username}"

        # suggest chat id based on the most recent chat
        suggested_values = {}
        description_placeholders["most_recent_chat"] = "Not available"
        try:
            most_recent_chat = await _get_most_recent_chat(service)
        except TelegramError as err:
            _LOGGER.warning("Error occurred while fetching recent chat: %s", err)
            most_recent_chat = None
        if most_recent_chat is not None:
            suggested_values[CONF_CHAT_ID] = most_recent_chat[0]

            description_placeholders["most_recent_chat"] = (
                f"{most_recent_chat[1]} ({most_recent_chat[0]})"
                if most_recent_chat[1]
                else str(most_recent_chat[0])
            )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                SUBENTRY_SCHEMA,
                suggested_values,
            ),
            description_placeholders=description_placeholders,
            errors=errors,
        )