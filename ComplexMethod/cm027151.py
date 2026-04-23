async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence."""
        conversation_id = user_input.conversation_id or ulid_util.ulid_now()
        intent_response = intent.IntentResponse(language=user_input.language)

        context = {"conversation_id": conversation_id}
        if user_input.satellite_id:
            context["satellite_id"] = user_input.satellite_id

        try:
            async with AsyncTcpClient(self.service.host, self.service.port) as client:
                await client.write_event(
                    Transcript(
                        user_input.text,
                        context=context,
                        language=user_input.language,
                    ).event()
                )

                while True:
                    event = await client.read_event()
                    if event is None:
                        _LOGGER.debug("Connection lost")
                        intent_response.async_set_error(
                            intent.IntentResponseErrorCode.UNKNOWN,
                            "Connection to service was lost",
                        )
                        return conversation.ConversationResult(
                            response=intent_response,
                            conversation_id=user_input.conversation_id,
                        )

                    if Intent.is_type(event.type):
                        # Success
                        recognized_intent = Intent.from_event(event)
                        _LOGGER.debug("Recognized intent: %s", recognized_intent)

                        intent_type = recognized_intent.name
                        intent_slots = {
                            e.name: {"value": e.value}
                            for e in recognized_intent.entities
                        }
                        intent_response = await intent.async_handle(
                            self.hass,
                            DOMAIN,
                            intent_type,
                            intent_slots,
                            text_input=user_input.text,
                            language=user_input.language,
                            satellite_id=user_input.satellite_id,
                            device_id=user_input.device_id,
                        )

                        if (not intent_response.speech) and recognized_intent.text:
                            intent_response.async_set_speech(recognized_intent.text)

                        break

                    if NotRecognized.is_type(event.type):
                        not_recognized = NotRecognized.from_event(event)
                        intent_response.async_set_error(
                            intent.IntentResponseErrorCode.NO_INTENT_MATCH,
                            not_recognized.text or "",
                        )
                        break

                    if Handled.is_type(event.type):
                        # Success
                        handled = Handled.from_event(event)
                        intent_response.async_set_speech(handled.text or "")
                        break

                    if NotHandled.is_type(event.type):
                        not_handled = NotHandled.from_event(event)
                        intent_response.async_set_error(
                            intent.IntentResponseErrorCode.FAILED_TO_HANDLE,
                            not_handled.text or "",
                        )
                        break

        except (OSError, WyomingError) as err:
            _LOGGER.exception("Unexpected error while communicating with service")
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Error communicating with service: {err}",
            )
            return conversation.ConversationResult(
                response=intent_response,
                conversation_id=user_input.conversation_id,
            )
        except intent.IntentError as err:
            _LOGGER.exception("Unexpected error while handling intent")
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.FAILED_TO_HANDLE,
                f"Error handling intent: {err}",
            )
            return conversation.ConversationResult(
                response=intent_response,
                conversation_id=user_input.conversation_id,
            )

        # Success
        return conversation.ConversationResult(
            response=intent_response, conversation_id=conversation_id
        )