async def read_response(response: StreamResponse, stream: bool, prompt: str, provider_info: dict, download_media: bool) -> AsyncResult:
    yield HeadersResponse.from_dict({key: value for key, value in response.headers.items() if key.lower().startswith("x-")})
    content_type = response.headers.get("content-type", "text/event-stream" if stream else "application/json")
    if content_type.startswith("application/json"):
        data = await response.json()
        if isinstance(data, list):
            data = next(iter(data), {})
        if isinstance(data, dict):
            yield JsonResponse.from_dict(data)
        OpenaiTemplate.raise_error(data, response.status)
        await raise_for_status(response)
        model = data.get("model")
        if model:
            yield ProviderInfo(**provider_info, model=model)
        if "usage" in data:
            yield Usage.from_dict(data["usage"])
        if "conversation" in data:
            yield JsonConversation.from_dict(data["conversation"])
        if "choices" in data:
            choice = next(iter(data["choices"]), None)
            message = choice.get("message", {})
            if choice and "content" in message and message["content"]:
                yield message["content"].strip()
            if "tool_calls" in message:
                yield ToolCalls(message["tool_calls"])
            if choice:
                reasoning_content = choice.get("delta", {}).get("reasoning_content", choice.get("delta", {}).get("reasoning"))
                if reasoning_content:
                    yield Reasoning(reasoning_content, status="")
            audio = message.get("audio", {})
            if "data" in audio:
                if download_media:
                    async for chunk in save_response_media(audio, prompt, [model]):
                        yield chunk
                else:
                    yield AudioResponse(f"data:audio/mpeg;base64,{audio['data']}", transcript=audio.get("transcript"))
            if choice and "finish_reason" in choice and choice["finish_reason"] is not None:
                yield FinishReason(choice["finish_reason"])
                return
    elif content_type.startswith("text/event-stream"):
        await raise_for_status(response)
        reasoning = False
        first = True
        model_returned = False
        async for data in sse_stream(response):
            yield JsonResponse.from_dict(data)
            OpenaiTemplate.raise_error(data)
            model = data.get("model")
            if not model_returned and model:
                yield ProviderInfo(**provider_info, model=model)
                model_returned = True
            choice = next(iter(data.get("choices", [])), None)
            if choice:
                content = choice.get("delta", {}).get("content")
                if content:
                    if first:
                        content = content.lstrip()
                    if content:
                        first = False
                        if reasoning:
                            yield Reasoning(status="")
                            reasoning = False
                        yield content
                tool_calls = choice.get("delta", {}).get("tool_calls")
                if tool_calls:
                    yield ToolCalls(tool_calls)
                reasoning_content = choice.get("delta", {}).get("reasoning_content", choice.get("delta", {}).get("reasoning"))
                if reasoning_content:
                    reasoning = True
                    yield Reasoning(reasoning_content)
            if "usage" in data and data["usage"] and "total_tokens" in data["usage"]:
                yield Usage.from_dict(data["usage"])
            if "conversation" in data and data["conversation"]:
                yield JsonConversation.from_dict(data["conversation"])
            if choice and choice.get("finish_reason") is not None:
                yield FinishReason(choice["finish_reason"])
    else:
        await raise_for_status(response)
        async for chunk in save_response_media(response, prompt, [model]):
            yield chunk