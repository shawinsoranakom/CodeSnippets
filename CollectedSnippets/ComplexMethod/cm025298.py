async def async_step_model(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Manage model-specific options."""
        options = self.options
        errors: dict[str, str] = {}

        step_schema: VolDictType = {}

        model = options[CONF_CHAT_MODEL]

        if not model.startswith(tuple(UNSUPPORTED_CODE_INTERPRETER_MODELS)):
            step_schema.update(
                {
                    vol.Optional(
                        CONF_CODE_INTERPRETER,
                        default=RECOMMENDED_CODE_INTERPRETER,
                    ): bool,
                }
            )
        elif CONF_CODE_INTERPRETER in options:
            options.pop(CONF_CODE_INTERPRETER)

        if reasoning_options := self._get_reasoning_options(model):
            step_schema.update(
                {
                    vol.Optional(
                        CONF_REASONING_EFFORT,
                        default=RECOMMENDED_REASONING_EFFORT,
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=reasoning_options,
                            translation_key=CONF_REASONING_EFFORT,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            )
        elif CONF_REASONING_EFFORT in options:
            options.pop(CONF_REASONING_EFFORT)

        if model.startswith("gpt-5"):
            step_schema.update(
                {
                    vol.Optional(
                        CONF_VERBOSITY,
                        default=RECOMMENDED_VERBOSITY,
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=["low", "medium", "high"],
                            translation_key=CONF_VERBOSITY,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(
                        CONF_REASONING_SUMMARY,
                        default=RECOMMENDED_REASONING_SUMMARY,
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=["off", "auto", "short", "detailed"],
                            translation_key=CONF_REASONING_SUMMARY,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            )
        elif CONF_VERBOSITY in options:
            options.pop(CONF_VERBOSITY)
        if CONF_REASONING_SUMMARY in options:
            if not model.startswith("gpt-5"):
                options.pop(CONF_REASONING_SUMMARY)

        service_tiers = self._get_service_tiers(model)
        if "flex" in service_tiers or "priority" in service_tiers:
            step_schema[
                vol.Optional(
                    CONF_SERVICE_TIER,
                    default=RECOMMENDED_SERVICE_TIER,
                )
            ] = SelectSelector(
                SelectSelectorConfig(
                    options=service_tiers,
                    translation_key=CONF_SERVICE_TIER,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        else:
            options.pop(CONF_SERVICE_TIER, None)
        if options.get(CONF_SERVICE_TIER) not in service_tiers:
            options.pop(CONF_SERVICE_TIER, None)

        if self._subentry_type == "conversation" and not model.startswith(
            tuple(UNSUPPORTED_WEB_SEARCH_MODELS)
        ):
            step_schema.update(
                {
                    vol.Optional(
                        CONF_WEB_SEARCH,
                        default=RECOMMENDED_WEB_SEARCH,
                    ): bool,
                    vol.Optional(
                        CONF_WEB_SEARCH_CONTEXT_SIZE,
                        default=RECOMMENDED_WEB_SEARCH_CONTEXT_SIZE,
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=["low", "medium", "high"],
                            translation_key=CONF_WEB_SEARCH_CONTEXT_SIZE,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(
                        CONF_WEB_SEARCH_USER_LOCATION,
                        default=RECOMMENDED_WEB_SEARCH_USER_LOCATION,
                    ): bool,
                    vol.Optional(
                        CONF_WEB_SEARCH_INLINE_CITATIONS,
                        default=RECOMMENDED_WEB_SEARCH_INLINE_CITATIONS,
                    ): bool,
                }
            )
        elif CONF_WEB_SEARCH in options:
            options = {
                k: v
                for k, v in options.items()
                if k
                not in (
                    CONF_WEB_SEARCH,
                    CONF_WEB_SEARCH_CONTEXT_SIZE,
                    CONF_WEB_SEARCH_USER_LOCATION,
                    CONF_WEB_SEARCH_CITY,
                    CONF_WEB_SEARCH_REGION,
                    CONF_WEB_SEARCH_COUNTRY,
                    CONF_WEB_SEARCH_TIMEZONE,
                    CONF_WEB_SEARCH_INLINE_CITATIONS,
                )
            }

        if self._subentry_type == "ai_task_data" and not model.startswith(
            tuple(UNSUPPORTED_IMAGE_MODELS)
        ):
            step_schema[
                vol.Optional(CONF_IMAGE_MODEL, default=RECOMMENDED_IMAGE_MODEL)
            ] = SelectSelector(
                SelectSelectorConfig(
                    options=[
                        "gpt-image-2",
                        "gpt-image-1.5",
                        "gpt-image-1",
                        "gpt-image-1-mini",
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )

        if user_input is not None:
            if user_input.get(CONF_WEB_SEARCH):
                if user_input.get(CONF_REASONING_EFFORT) == "minimal":
                    errors[CONF_WEB_SEARCH] = "web_search_minimal_reasoning"
                if user_input.get(CONF_WEB_SEARCH_USER_LOCATION) and not errors:
                    user_input.update(await self._get_location_data())
                else:
                    options.pop(CONF_WEB_SEARCH_CITY, None)
                    options.pop(CONF_WEB_SEARCH_REGION, None)
                    options.pop(CONF_WEB_SEARCH_COUNTRY, None)
                    options.pop(CONF_WEB_SEARCH_TIMEZONE, None)
            if (
                user_input.get(CONF_CODE_INTERPRETER)
                and user_input.get(CONF_REASONING_EFFORT) == "minimal"
            ):
                errors[CONF_CODE_INTERPRETER] = "code_interpreter_minimal_reasoning"

            options.update(user_input)
            if not errors:
                if self._is_new:
                    return self.async_create_entry(
                        title=options.pop(CONF_NAME),
                        data=options,
                    )
                return self.async_update_and_abort(
                    self._get_entry(),
                    self._get_reconfigure_subentry(),
                    data=options,
                )

        return self.async_show_form(
            step_id="model",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(step_schema), options
            ),
            errors=errors,
        )