async def async_step_model(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Manage model-specific options."""
        errors: dict[str, str] = {}

        step_schema: VolDictType = {
            vol.Optional(
                CONF_MAX_TOKENS,
                default=DEFAULT[CONF_MAX_TOKENS],
            ): vol.All(
                NumberSelector(
                    NumberSelectorConfig(min=0, max=self.model_info.max_tokens)
                ),
                vol.Coerce(int),
            )
            if self.model_info.max_tokens
            else cv.positive_int,
        }

        if (
            self.model_info.capabilities
            and self.model_info.capabilities.thinking.supported
            and not self.model_info.capabilities.thinking.types.adaptive.supported
        ):
            step_schema[
                vol.Optional(
                    CONF_THINKING_BUDGET, default=DEFAULT[CONF_THINKING_BUDGET]
                )
            ] = (
                vol.All(
                    NumberSelector(
                        NumberSelectorConfig(min=0, max=self.model_info.max_tokens)
                    ),
                    vol.Coerce(int),
                )
                if self.model_info.max_tokens
                else cv.positive_int
            )
        else:
            self.options.pop(CONF_THINKING_BUDGET, None)

        if (
            self.model_info.capabilities
            and (effort_capability := self.model_info.capabilities.effort).supported
        ):
            effort_options: list[str] = []
            if self.model_info.capabilities.thinking.types.adaptive.supported:
                effort_options.append("none")
            if effort_capability.low.supported:
                effort_options.append("low")
            if effort_capability.medium.supported:
                effort_options.append("medium")
            if effort_capability.high.supported:
                effort_options.append("high")
            if effort_capability.xhigh and effort_capability.xhigh.supported:
                effort_options.append("xhigh")
            if effort_capability.max.supported:
                effort_options.append("max")
            step_schema[
                vol.Optional(
                    CONF_THINKING_EFFORT,
                    default=DEFAULT[CONF_THINKING_EFFORT],
                )
            ] = SelectSelector(
                SelectSelectorConfig(
                    options=effort_options,
                    translation_key=CONF_THINKING_EFFORT,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        else:
            self.options.pop(CONF_THINKING_EFFORT, None)

        step_schema.update(
            {
                vol.Optional(
                    CONF_CODE_EXECUTION,
                    default=DEFAULT[CONF_CODE_EXECUTION],
                ): bool,
                vol.Optional(
                    CONF_WEB_SEARCH,
                    default=DEFAULT[CONF_WEB_SEARCH],
                ): bool,
                vol.Optional(
                    CONF_WEB_SEARCH_MAX_USES,
                    default=DEFAULT[CONF_WEB_SEARCH_MAX_USES],
                ): int,
                vol.Optional(
                    CONF_WEB_SEARCH_USER_LOCATION,
                    default=DEFAULT[CONF_WEB_SEARCH_USER_LOCATION],
                ): bool,
            }
        )

        self.options.pop(CONF_WEB_SEARCH_CITY, None)
        self.options.pop(CONF_WEB_SEARCH_REGION, None)
        self.options.pop(CONF_WEB_SEARCH_COUNTRY, None)
        self.options.pop(CONF_WEB_SEARCH_TIMEZONE, None)

        model = self.options[CONF_CHAT_MODEL]

        if not model.startswith(tuple(TOOL_SEARCH_UNSUPPORTED_MODELS)):
            step_schema[
                vol.Optional(
                    CONF_TOOL_SEARCH,
                    default=DEFAULT[CONF_TOOL_SEARCH],
                )
            ] = bool
        else:
            self.options.pop(CONF_TOOL_SEARCH, None)

        if not step_schema:
            # Currently our schema is always present, but if one day it becomes empty,
            # then the below line is needed to skip this step
            user_input = {}  # pragma: no cover

        if user_input is not None:
            if (
                CONF_THINKING_BUDGET in user_input
                and user_input[CONF_THINKING_BUDGET] >= MIN_THINKING_BUDGET
                and user_input[CONF_THINKING_BUDGET]
                >= user_input.get(CONF_MAX_TOKENS, DEFAULT[CONF_MAX_TOKENS])
            ):
                errors[CONF_THINKING_BUDGET] = "thinking_budget_too_large"

            if user_input.get(CONF_WEB_SEARCH, DEFAULT[CONF_WEB_SEARCH]) and not errors:
                if user_input.get(
                    CONF_WEB_SEARCH_USER_LOCATION,
                    DEFAULT[CONF_WEB_SEARCH_USER_LOCATION],
                ):
                    user_input.update(await self._get_location_data())

            self.options.update(user_input)

            if not errors:
                if self._is_new:
                    return self.async_create_entry(
                        title=self.options.pop(CONF_NAME),
                        data=self.options,
                    )

                return self.async_update_and_abort(
                    self._get_entry(),
                    self._get_reconfigure_subentry(),
                    data=self.options,
                )

        return self.async_show_form(
            step_id="model",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(step_schema), self.options
            ),
            errors=errors or None,
            last_step=True,
        )