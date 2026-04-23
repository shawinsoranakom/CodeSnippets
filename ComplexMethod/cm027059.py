async def async_step_api(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._async_abort_entries_match(user_input)
            try:
                await validate_input(self.hass, user_input)
            except (APIError, Timeout) as err:
                if isinstance(err, ClientError) and "API_KEY_INVALID" in str(err):
                    errors["base"] = "invalid_auth"
                else:
                    errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                if self.source == SOURCE_REAUTH:
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(),
                        data=user_input,
                    )
                return self.async_create_entry(
                    title=DEFAULT_TITLE,
                    data=user_input,
                    subentries=[
                        {
                            "subentry_type": "conversation",
                            "data": RECOMMENDED_CONVERSATION_OPTIONS,
                            "title": DEFAULT_CONVERSATION_NAME,
                            "unique_id": None,
                        },
                        {
                            "subentry_type": "tts",
                            "data": RECOMMENDED_TTS_OPTIONS,
                            "title": DEFAULT_TTS_NAME,
                            "unique_id": None,
                        },
                        {
                            "subentry_type": "ai_task_data",
                            "data": RECOMMENDED_AI_TASK_OPTIONS,
                            "title": DEFAULT_AI_TASK_NAME,
                            "unique_id": None,
                        },
                        {
                            "subentry_type": "stt",
                            "data": RECOMMENDED_STT_OPTIONS,
                            "title": DEFAULT_STT_NAME,
                            "unique_id": None,
                        },
                    ],
                )
        return self.async_show_form(
            step_id="api",
            data_schema=STEP_API_DATA_SCHEMA,
            description_placeholders={
                "api_key_url": "https://aistudio.google.com/app/apikey"
            },
            errors=errors,
        )