def iter_response(
    response: Union[Iterator[Union[str, ResponseType]]],
    stream: bool,
    response_format: Optional[dict] = None,
    max_tokens: Optional[int] = None,
    stop: Optional[list[str]] = None,
    provider_info: Optional[ProviderInfo] = None
) -> ChatCompletionResponseType:
    content = ""
    reasoning = []
    finish_reason = None
    tool_calls = None
    usage = None
    provider_info: ProviderInfo = None
    conversation: JsonConversation = None
    completion_id = ''.join(random.choices(string.ascii_letters + string.digits, k=28))
    idx = 0

    if hasattr(response, '__aiter__'):
        response = to_sync_generator(response)

    for chunk in response:
        if isinstance(chunk, FinishReason):
            finish_reason = chunk.reason
            continue
        elif isinstance(chunk, JsonConversation):
            conversation = chunk
            continue
        elif isinstance(chunk, ToolCalls):
            if not stream:
                tool_calls = chunk.get_list()
                continue
        elif isinstance(chunk, Usage):
            usage = chunk
            continue
        elif isinstance(chunk, ProviderInfo):
            provider_info = chunk
            continue
        elif isinstance(chunk, Reasoning):
            reasoning.append(chunk)
        elif isinstance(chunk, (HiddenResponse, Exception, JsonRequest, JsonResponse)):
            continue
        elif not chunk:
            continue

        content = add_chunk(content, chunk)
        idx += 1

        if max_tokens is not None and idx >= max_tokens:
            finish_reason = "length"

        first, content, chunk = find_stop(stop, content, chunk if stream else None)

        if first != -1:
            finish_reason = "stop"

        if stream:
            chunk = ChatCompletionChunk.model_construct(chunk, None, completion_id, int(time.time()))
            if provider_info is not None:
                chunk.provider = provider_info.name
                chunk.model = provider_info.model
            yield chunk

        if finish_reason is not None:
            break

    if usage is None:
        usage = UsageModel.model_construct(completion_tokens=idx, total_tokens=idx)
    else:
        usage = UsageModel.model_construct(**usage.get_dict())

    finish_reason = "tool_calls" if tool_calls else ("stop" if finish_reason is None else finish_reason)

    if stream:
        chat_completion = ChatCompletionChunk.model_construct(
            None, finish_reason, completion_id, int(time.time()), usage=usage
        )
    else:
        if response_format is not None and "type" in response_format:
            if response_format["type"] == "json_object":
                content = filter_json(content)
        chat_completion = ChatCompletion.model_construct(
            content, finish_reason, completion_id, int(time.time()), usage=usage,
            **(filter_none(
                tool_calls=[ToolCallModel.model_construct(**tool_call) for tool_call in tool_calls]
            ) if tool_calls is not None else {}),
            conversation=None if conversation is None else conversation.get_dict(),
            reasoning=reasoning if reasoning else None
        )
    if provider_info is not None:
        chat_completion.provider = provider_info.name
        chat_completion.model = provider_info.model
    yield chat_completion