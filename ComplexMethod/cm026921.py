async def async_provide_llm_data(
        self,
        llm_context: llm.LLMContext,
        user_llm_hass_api: str | list[str] | llm.API | None = None,
        user_llm_prompt: str | None = None,
        user_extra_system_prompt: str | None = None,
    ) -> None:
        """Set the LLM system prompt."""
        llm_api: llm.APIInstance | None = None

        if not user_llm_hass_api:
            pass
        elif isinstance(user_llm_hass_api, llm.API):
            llm_api = await user_llm_hass_api.async_get_api_instance(llm_context)
        else:
            try:
                llm_api = await llm.async_get_api(
                    self.hass,
                    user_llm_hass_api,
                    llm_context,
                )
            except HomeAssistantError as err:
                LOGGER.error(
                    "Error getting LLM API %s for %s: %s",
                    user_llm_hass_api,
                    llm_context.platform,
                    err,
                )
                intent_response = intent.IntentResponse(
                    language=llm_context.language or ""
                )
                intent_response.async_set_error(
                    intent.IntentResponseErrorCode.UNKNOWN,
                    "Error preparing LLM API",
                )
                raise ConverseError(
                    f"Error getting LLM API {user_llm_hass_api}",
                    conversation_id=self.conversation_id,
                    response=intent_response,
                ) from err

        user_name: str | None = None

        if (
            llm_context.context
            and llm_context.context.user_id
            and (
                user := await self.hass.auth.async_get_user(llm_context.context.user_id)
            )
        ):
            user_name = user.name

        prompt_parts = []
        prompt_parts.append(
            await self._async_expand_prompt_template(
                llm_context,
                (user_llm_prompt or llm.DEFAULT_INSTRUCTIONS_PROMPT),
                llm_context.language,
                user_name,
            )
        )

        if llm_api:
            prompt_parts.append(llm_api.api_prompt)

        # Append current date and time to the prompt if the corresponding tool is not provided
        llm_tools: list[llm.Tool] = llm_api.tools if llm_api else []
        if not any(tool.name.endswith("GetDateTime") for tool in llm_tools):
            prompt_parts.append(
                await self._async_expand_prompt_template(
                    llm_context,
                    llm.DATE_TIME_PROMPT,
                    llm_context.language,
                    user_name,
                )
            )

        if extra_system_prompt := (
            # Take new system prompt if one was given
            user_extra_system_prompt or self.extra_system_prompt
        ):
            prompt_parts.append(extra_system_prompt)

        prompt = "\n".join(prompt_parts)

        self.llm_input_provided_index = len(self.content)
        self.llm_api = llm_api
        self.extra_system_prompt = extra_system_prompt
        self.content[0] = SystemContent(content=prompt)
        _async_notify_subscribers(
            self.hass,
            self.conversation_id,
            ChatLogEventType.UPDATED,
            {"chat_log": self.as_dict()},
        )

        LOGGER.debug("Prompt: %s", self.content)
        LOGGER.debug("Tools: %s", self.llm_api.tools if self.llm_api else None)

        self.async_trace(
            {
                "messages": self.content,
                "tools": self.llm_api.tools if self.llm_api else None,
            }
        )