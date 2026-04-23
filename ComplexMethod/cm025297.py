async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Manage initial options."""
        # abort if entry is not loaded
        if self._get_entry().state != ConfigEntryState.LOADED:
            return self.async_abort(reason="entry_not_loaded")

        options = self.options

        hass_apis: list[SelectOptionDict] = [
            SelectOptionDict(
                label=api.name,
                value=api.id,
            )
            for api in llm.async_get_apis(self.hass)
        ]
        if suggested_llm_apis := options.get(CONF_LLM_HASS_API):
            if isinstance(suggested_llm_apis, str):
                suggested_llm_apis = [suggested_llm_apis]
            valid_apis = {api.id for api in llm.async_get_apis(self.hass)}
            options[CONF_LLM_HASS_API] = [
                api for api in suggested_llm_apis if api in valid_apis
            ]

        step_schema: VolDictType = {}

        if self._is_new:
            if self._subentry_type == "ai_task_data":
                default_name = DEFAULT_AI_TASK_NAME
            else:
                default_name = DEFAULT_CONVERSATION_NAME
            step_schema[vol.Required(CONF_NAME, default=default_name)] = str

        if self._subentry_type == "conversation":
            step_schema.update(
                {
                    vol.Optional(
                        CONF_PROMPT,
                        description={
                            "suggested_value": options.get(
                                CONF_PROMPT, llm.DEFAULT_INSTRUCTIONS_PROMPT
                            )
                        },
                    ): TemplateSelector(),
                    vol.Optional(CONF_LLM_HASS_API): SelectSelector(
                        SelectSelectorConfig(options=hass_apis, multiple=True)
                    ),
                }
            )

        step_schema[
            vol.Required(CONF_RECOMMENDED, default=options.get(CONF_RECOMMENDED, False))
        ] = bool

        if user_input is not None:
            if not user_input.get(CONF_LLM_HASS_API):
                user_input.pop(CONF_LLM_HASS_API, None)

            if user_input[CONF_RECOMMENDED]:
                if self._is_new:
                    return self.async_create_entry(
                        title=user_input.pop(CONF_NAME),
                        data=user_input,
                    )
                return self.async_update_and_abort(
                    self._get_entry(),
                    self._get_reconfigure_subentry(),
                    data=user_input,
                )

            options.update(user_input)
            if CONF_LLM_HASS_API in options and CONF_LLM_HASS_API not in user_input:
                options.pop(CONF_LLM_HASS_API)
            return await self.async_step_advanced()

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(step_schema), options
            ),
        )