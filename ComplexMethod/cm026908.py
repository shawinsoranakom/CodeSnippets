async def _async_process_intent_result(
        self,
        result: RecognizeResult | None,
        user_input: ConversationInput,
        chat_log: ChatLog,
    ) -> intent.IntentResponse:
        """Process user input with intents."""
        language = user_input.language or self.hass.config.language

        # Intent match or failure
        lang_intents = await self.async_get_or_load_intents(language)

        if result is None:
            # Intent was not recognized
            _LOGGER.debug("No intent was matched for '%s'", user_input.text)
            return _make_error_result(
                language,
                intent.IntentResponseErrorCode.NO_INTENT_MATCH,
                self._get_error_text(ErrorKey.NO_INTENT, lang_intents),
            )

        if result.unmatched_entities:
            # Intent was recognized, but not entity/area names, etc.
            _LOGGER.debug(
                "Recognized intent '%s' for template '%s' but had unmatched: %s",
                result.intent.name,
                (
                    result.intent_sentence.text
                    if result.intent_sentence is not None
                    else ""
                ),
                result.unmatched_entities_list,
            )
            error_response_type, error_response_args = _get_unmatched_response(result)
            return _make_error_result(
                language,
                intent.IntentResponseErrorCode.NO_VALID_TARGETS,
                self._get_error_text(
                    error_response_type, lang_intents, **error_response_args
                ),
            )

        # Will never happen because result will be None when no intents are
        # loaded in async_recognize.
        assert lang_intents is not None

        # Slot values to pass to the intent
        slots: dict[str, Any] = {
            entity.name: {
                "value": entity.value,
                "text": entity.text or entity.value,
            }
            for entity in result.entities_list
        }

        satellite_id = user_input.satellite_id
        device_id = user_input.device_id
        satellite_area, device_id = self._get_satellite_area_and_device(
            satellite_id, device_id
        )
        if satellite_area is not None:
            slots["preferred_area_id"] = {"value": satellite_area.id}

        async_conversation_trace_append(
            ConversationTraceEventType.TOOL_CALL,
            {
                "intent_name": result.intent.name,
                "slots": {entity.name: entity.value for entity in result.entities_list},
            },
        )
        tool_input = llm.ToolInput(
            tool_name=result.intent.name,
            tool_args={entity.name: entity.value for entity in result.entities_list},
            external=True,
        )
        chat_log.async_add_assistant_content_without_tools(
            AssistantContent(
                agent_id=user_input.agent_id,
                content=None,
                tool_calls=[tool_input],
            )
        )

        try:
            intent_response = await intent.async_handle(
                self.hass,
                DOMAIN,
                result.intent.name,
                slots,
                user_input.text,
                user_input.context,
                language,
                assistant=DOMAIN,
                device_id=device_id,
                satellite_id=satellite_id,
                conversation_agent_id=user_input.agent_id,
            )
        except intent.MatchFailedError as match_error:
            # Intent was valid, but no entities matched the constraints.
            error_response_type, error_response_args = _get_match_error_response(
                self.hass, match_error
            )
            intent_response = _make_error_result(
                language,
                intent.IntentResponseErrorCode.NO_VALID_TARGETS,
                self._get_error_text(
                    error_response_type, lang_intents, **error_response_args
                ),
            )
        except intent.IntentHandleError as err:
            # Intent was valid and entities matched constraints, but an error
            # occurred during handling.
            _LOGGER.exception("Intent handling error")
            intent_response = _make_error_result(
                language,
                intent.IntentResponseErrorCode.FAILED_TO_HANDLE,
                self._get_error_text(
                    err.response_key or ErrorKey.HANDLE_ERROR, lang_intents
                ),
            )
        except intent.IntentUnexpectedError:
            _LOGGER.exception("Unexpected intent error")
            intent_response = _make_error_result(
                language,
                intent.IntentResponseErrorCode.UNKNOWN,
                self._get_error_text(ErrorKey.HANDLE_ERROR, lang_intents),
            )

        if (
            (not intent_response.speech)
            and (intent_response.intent is not None)
            and (response_key := result.response)
        ):
            # Use response template, if available
            response_template_str = lang_intents.intent_responses.get(
                result.intent.name, {}
            ).get(response_key)
            if response_template_str:
                response_template = template.Template(response_template_str, self.hass)
                speech = await self._build_speech(
                    language, response_template, intent_response, result
                )
                intent_response.async_set_speech(speech)

        tool_result = llm.IntentResponseDict(intent_response)
        chat_log.async_add_assistant_content_without_tools(
            ToolResultContent(
                agent_id=user_input.agent_id,
                tool_call_id=tool_input.id,
                tool_name=tool_input.tool_name,
                tool_result=tool_result,
            )
        )

        return intent_response