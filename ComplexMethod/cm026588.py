async def async_step_advanced(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Manage advanced options."""
        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = {}

        step_schema: VolDictType = {
            vol.Optional(
                CONF_CHAT_MODEL,
                default=DEFAULT[CONF_CHAT_MODEL],
            ): SelectSelector(
                SelectSelectorConfig(options=self._get_model_list(), custom_value=True)
            ),
            vol.Optional(
                CONF_PROMPT_CACHING,
                default=DEFAULT[CONF_PROMPT_CACHING],
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[x.value for x in PromptCaching],
                    translation_key=CONF_PROMPT_CACHING,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }

        if user_input is not None:
            self.options.update(user_input)

            coordinator = self._get_entry().runtime_data
            self.model_info, status = coordinator.get_model_info(
                self.options[CONF_CHAT_MODEL]
            )
            if not status:
                # Couldn't find the model in the cached list, try to fetch it directly
                client = coordinator.client
                try:
                    self.model_info = await client.models.retrieve(
                        self.options[CONF_CHAT_MODEL], timeout=10.0
                    )
                except anthropic.NotFoundError:
                    errors[CONF_CHAT_MODEL] = "model_not_found"
                except anthropic.AnthropicError as err:
                    errors[CONF_CHAT_MODEL] = "api_error"
                    description_placeholders["message"] = (
                        err.message if isinstance(err, anthropic.APIError) else str(err)
                    )

            if not errors:
                return await self.async_step_model()

        return self.async_show_form(
            step_id="advanced",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(step_schema), self.options
            ),
            errors=errors,
            description_placeholders=description_placeholders,
        )