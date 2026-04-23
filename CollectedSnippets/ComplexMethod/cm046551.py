def _normalise_responses_input(payload: ResponsesRequest) -> list[ChatMessage]:
    """Convert a ResponsesRequest's ``input`` into Chat-format ``ChatMessage`` list.

    Handles the three input item shapes allowed by the Responses API:

    - ``ResponsesInputMessage`` — regular chat messages (text or multimodal).
    - ``ResponsesFunctionCallInputItem`` — a prior assistant tool call replayed
      on a follow-up turn. Converted into an assistant message carrying a
      Chat Completions ``tool_calls`` entry keyed by ``call_id``.
    - ``ResponsesFunctionCallOutputInputItem`` — a tool result the client is
      returning. Converted into a ``role="tool"`` message with ``tool_call_id``
      set to the originating ``call_id`` so llama-server can reconcile the
      call with its result.

    System / developer content is collected from ``instructions`` *and* from
    any ``role="system"`` / ``role="developer"`` entries in ``input``, then
    merged into a single ``role="system"`` message placed at the top of the
    returned list. This satisfies strict chat templates (harmony / gpt-oss,
    Qwen3, ...) whose Jinja raises ``"System message must be at the
    beginning."`` when more than one system message is present or when a
    system message appears after a user turn — the exact pattern the OpenAI
    Codex CLI hits, since Codex sets ``instructions`` *and* also sends a
    developer message in ``input``.
    """
    system_parts: list[str] = []
    messages: list[ChatMessage] = []

    if payload.instructions:
        system_parts.append(payload.instructions)

    # Simple string input
    if isinstance(payload.input, str):
        if payload.input:
            messages.append(ChatMessage(role = "user", content = payload.input))
        if system_parts:
            merged = "\n\n".join(p for p in system_parts if p)
            return [ChatMessage(role = "system", content = merged), *messages]
        return messages

    for item in payload.input:
        if isinstance(item, ResponsesFunctionCallInputItem):
            messages.append(
                ChatMessage(
                    role = "assistant",
                    content = None,
                    tool_calls = [
                        {
                            "id": item.call_id,
                            "type": "function",
                            "function": {
                                "name": item.name,
                                "arguments": item.arguments,
                            },
                        }
                    ],
                )
            )
            continue

        if isinstance(item, ResponsesFunctionCallOutputInputItem):
            # Chat Completions `role="tool"` requires a string content; if a
            # Responses client sends a content-array output, serialize it.
            output = item.output
            if not isinstance(output, str):
                output = json.dumps(output)
            messages.append(
                ChatMessage(
                    role = "tool",
                    tool_call_id = item.call_id,
                    content = output,
                )
            )
            continue

        if isinstance(item, ResponsesUnknownInputItem):
            # Reasoning items and any other unmodelled top-level Responses
            # item types are silently dropped — llama-server-backed GGUFs
            # cannot consume them and our lenient validation let them in so
            # unrelated turns don't 422.
            continue

        # ResponsesInputMessage — hoist system/developer to the top, merge.
        if item.role in ("system", "developer"):
            hoisted = _responses_message_text(item.content)
            if hoisted:
                system_parts.append(hoisted)
            continue

        if isinstance(item.content, str):
            messages.append(ChatMessage(role = item.role, content = item.content))
            continue

        # Assistant-replay turns come back as content = [output_text, ...].
        # Chat Completions' assistant role expects a plain string, not a
        # multimodal content array, so flatten output_text (and any stray
        # input_text / unknown text) to a single string.
        if item.role == "assistant":
            text = _responses_message_text(item.content)
            if text:
                messages.append(ChatMessage(role = "assistant", content = text))
            continue

        # User (and any other remaining roles) — keep multimodal when
        # present, drop unknown content parts silently.
        parts: list = []
        for part in item.content:
            if isinstance(part, (ResponsesInputTextPart, ResponsesOutputTextPart)):
                parts.append(TextContentPart(type = "text", text = part.text))
            elif isinstance(part, ResponsesInputImagePart):
                parts.append(
                    ImageContentPart(
                        type = "image_url",
                        image_url = ImageUrl(url = part.image_url, detail = part.detail),
                    )
                )
            # ResponsesUnknownContentPart and anything else: drop.
        if parts:
            # Collapse single-text-part content to a plain string so roles
            # that reject multimodal arrays (e.g. legacy templates) still
            # accept the message.
            if len(parts) == 1 and isinstance(parts[0], TextContentPart):
                messages.append(ChatMessage(role = item.role, content = parts[0].text))
            else:
                messages.append(ChatMessage(role = item.role, content = parts))

    if system_parts:
        merged = "\n\n".join(p for p in system_parts if p)
        return [ChatMessage(role = "system", content = merged), *messages]
    return messages