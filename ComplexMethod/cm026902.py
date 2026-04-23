async def call_action(
        user_input: ConversationInput, result: RecognizeResult
    ) -> str | None:
        """Call action with right context."""

        # Add slot values as extra trigger data
        details = {
            entity_name: {
                "name": entity_name,
                "text": entity.text.strip(),  # remove whitespace
                "value": (
                    entity.value.strip()
                    if isinstance(entity.value, str)
                    else entity.value
                ),
            }
            for entity_name, entity in result.entities.items()
        }

        satellite_id = user_input.satellite_id
        device_id = user_input.device_id
        if (
            satellite_id is not None
            and (satellite_entry := ent_reg.async_get(satellite_id)) is not None
        ):
            device_id = satellite_entry.device_id

        trigger_input: dict[str, Any] = {  # Satisfy type checker
            **trigger_data,
            "platform": DOMAIN,
            "sentence": user_input.text,
            "details": details,
            "slots": {  # direct access to values
                entity_name: entity["value"] for entity_name, entity in details.items()
            },
            "device_id": device_id,
            "satellite_id": satellite_id,
            "user_input": user_input.as_dict(),
        }

        # Wait for the automation to complete
        if future := hass.async_run_hass_job(
            job,
            {"trigger": trigger_input},
        ):
            automation_result = await future
            if isinstance(
                automation_result, ScriptRunResult
            ) and automation_result.conversation_response not in (None, UNDEFINED):
                # mypy does not understand the type narrowing, unclear why
                return automation_result.conversation_response  # type: ignore[return-value]

        # It's important to return None here instead of a string.
        #
        # When editing in the UI, a copy of this trigger is registered.
        # If we return a string from here, there is a race condition between the
        # two trigger copies for who will provide a response.
        return None