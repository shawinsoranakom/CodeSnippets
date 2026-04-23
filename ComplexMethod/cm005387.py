def _normalize_input(body: dict) -> list[dict]:
        """Normalize the Responses API ``input`` field into chat messages.

        The Responses API accepts multiple input formats. This method converts them
        into a structure close to what ``apply_chat_template`` expects (messages with
        ``role``, ``content``, ``tool_calls``, ``tool_call_id``). Further processing
        is done by ``get_processor_inputs_from_messages``.

        NOTE: if this conversion logic grows too complex, consider having separate
        ``get_processor_inputs_from_messages`` implementations for chat completions
        and the Responses API instead of funneling both through the same path.

        Formats handled:
            - **String** → single user message.
            - **Flat content list** (``input_text``, ``input_image``, no ``role``) → user message.
            - **Multi-turn list** — messages and tool call items (``function_call``,
              ``function_call_output``) from a previous response, converted via
              :meth:`_normalize_response_items`.

        If ``instructions`` is present, it is prepended as a system message.
        """
        inp = body["input"]
        instructions = body.get("instructions")

        if isinstance(inp, str):
            messages = [{"role": "user", "content": inp}]
        elif isinstance(inp, list):
            if inp and "role" not in inp[0]:
                # Flat content list (single-turn, e.g. input_text/input_image)
                messages = [{"role": "user", "content": inp}]
            else:
                messages = ResponseHandler._normalize_response_items(inp)
        else:
            raise HTTPException(status_code=422, detail="'input' must be a string or list")

        # Prepend instructions as a system message
        if instructions:
            if messages and messages[0]["role"] == "system":
                messages[0]["content"] = instructions
            else:
                messages.insert(0, {"role": "system", "content": instructions})

        return messages