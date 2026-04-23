async def _async_send_telegram_message(service: ServiceCall) -> ServiceResponse:
    """Handle sending Telegram Bot message service calls."""

    _deprecate_timeout(service)

    # this is the list of targets to send the message to
    targets = _build_targets(service)

    service_responses: JsonValueType = []
    errors: list[tuple[Exception, str]] = []

    # invoke the service for each target
    for target_config_entry, target_chat_id, target_notify_entity_id in targets:
        try:
            service_response = await _call_service(
                service, target_config_entry.runtime_data, target_chat_id
            )

            if service.service == SERVICE_DOWNLOAD_FILE:
                return service_response

            if service_response is not None:
                formatted_responses: list[JsonValueType] = []
                for chat_id, message_id in service_response.items():
                    formatted_response = {
                        ATTR_CHAT_ID: int(chat_id),
                        ATTR_MESSAGE_ID: message_id,
                    }

                    if target_notify_entity_id:
                        formatted_response[ATTR_ENTITY_ID] = target_notify_entity_id

                    formatted_responses.append(formatted_response)

                assert isinstance(service_responses, list)
                service_responses.extend(formatted_responses)
        except (HomeAssistantError, TelegramError) as ex:
            target = target_notify_entity_id or str(target_chat_id)
            errors.append((ex, target))

    if len(errors) == 1:
        if isinstance(errors[0][0], HomeAssistantError):
            raise errors[0][0]
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="action_failed",
            translation_placeholders={"error": str(errors[0][0])},
        ) from errors[0][0]

    if len(errors) > 1:
        error_messages: list[str] = []
        for error, target in errors:
            target_type = ATTR_CHAT_ID if target.isdigit() else ATTR_ENTITY_ID
            error_messages.append(f"`{target_type}` {target}: {error}")

        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="multiple_errors",
            translation_placeholders={"errors": "\n".join(error_messages)},
        )

    if service.return_response:
        return {"chats": service_responses}

    return None