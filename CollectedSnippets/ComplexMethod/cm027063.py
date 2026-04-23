async def _transform_stream(
    result: AsyncIterator[GenerateContentResponse],
) -> AsyncGenerator[conversation.AssistantContentDeltaDict]:
    new_message = True
    part_details: list[PartDetails] = []
    try:
        async for response in result:
            LOGGER.debug("Received response chunk: %s", response)

            if new_message:
                if part_details:
                    yield {"native": ContentDetails(part_details=part_details)}
                    part_details = []
                yield {"role": "assistant"}
                new_message = False
                content_index = 0
                thinking_content_index = 0
                tool_call_index = 0

            # According to the API docs, this would mean no candidate is returned, so we can safely throw an error here.
            if response.prompt_feedback or not response.candidates:
                reason = (
                    response.prompt_feedback.block_reason_message
                    if response.prompt_feedback
                    else "unknown"
                )
                raise HomeAssistantError(
                    f"The message got blocked due to content violations, reason: {reason}"
                )

            candidate = response.candidates[0]

            if (
                candidate.finish_reason is not None
                and candidate.finish_reason != "STOP"
            ):
                # The message ended due to a content error as explained in: https://ai.google.dev/api/generate-content#FinishReason
                LOGGER.error(
                    "Error in Google Generative AI response: %s, see: https://ai.google.dev/api/generate-content#FinishReason",
                    candidate.finish_reason,
                )
                raise HomeAssistantError(
                    f"{ERROR_GETTING_RESPONSE} Reason: {candidate.finish_reason}"
                )

            response_parts = (
                candidate.content.parts
                if candidate.content is not None and candidate.content.parts is not None
                else []
            )

            for part in response_parts:
                chunk: conversation.AssistantContentDeltaDict = {}

                if part.text:
                    if part.thought:
                        chunk["thinking_content"] = part.text
                        if part.thought_signature:
                            part_details.append(
                                PartDetails(
                                    part_type="thought",
                                    index=thinking_content_index,
                                    length=len(part.text),
                                    thought_signature=base64.b64encode(
                                        part.thought_signature
                                    ).decode("utf-8"),
                                )
                            )
                        thinking_content_index += len(part.text)
                    else:
                        chunk["content"] = part.text
                        if part.thought_signature:
                            part_details.append(
                                PartDetails(
                                    part_type="text",
                                    index=content_index,
                                    length=len(part.text),
                                    thought_signature=base64.b64encode(
                                        part.thought_signature
                                    ).decode("utf-8"),
                                )
                            )
                        content_index += len(part.text)

                if part.function_call:
                    tool_call = part.function_call
                    tool_name = tool_call.name or ""
                    tool_args = _escape_decode(tool_call.args)
                    chunk["tool_calls"] = [
                        llm.ToolInput(tool_name=tool_name, tool_args=tool_args)
                    ]
                    if part.thought_signature:
                        part_details.append(
                            PartDetails(
                                part_type="function_call",
                                index=tool_call_index,
                                thought_signature=base64.b64encode(
                                    part.thought_signature
                                ).decode("utf-8"),
                            )
                        )

                yield chunk

        if part_details:
            yield {"native": ContentDetails(part_details=part_details)}

    except (
        APIError,
        ValueError,
    ) as err:
        LOGGER.error("Error sending message: %s %s", type(err), err)
        if isinstance(err, APIError):
            message = err.message
        else:
            message = type(err).__name__
        error = f"{ERROR_GETTING_RESPONSE}: {message}"
        raise HomeAssistantError(error) from err