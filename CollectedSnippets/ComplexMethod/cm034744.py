async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        prompt: str = None,
        proxy: str = None,
        stream: bool = True,
        api_key: str = None,
        media: MediaListType = None,
        extra_parameters: list[str] = ["temperature", "presence_penalty", "top_p", "frequency_penalty", "response_format", "tools", "parallel_tool_calls", "tool_choice", "reasoning_effort", "logit_bias", "voice", "modalities", "audio"],
        **kwargs
    ) -> AsyncResult:
        if not api_key:
            raise MissingAuthError("API key is required for Puter.js API")

        if not cls.models:
            cls.get_models()

        # Check if we need to use a vision model
        if not model and media is not None and len(media) > 0:
            model = cls.default_vision_model

        # Check for image URLs in messages
        if not model:
            for msg in messages:
                if msg["role"] == "user":
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        for item in content:
                            if item.get("type") == "image_url":
                                model = cls.default_vision_model
                                break

        # Get the model name from the user-provided model
        try:
            model = cls.get_model(model)
        except ModelNotFoundError:
            pass

        async with ClientSession() as session:
            headers = {
                "authorization": f"Bearer {api_key}",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
                "content-type": "application/json;charset=UTF-8",
                # Set appropriate accept header based on stream mode
                "accept": "text/event-stream" if stream else "*/*",
                "origin": "http://docs.puter.com",
                "sec-fetch-site": "cross-site",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "http://docs.puter.com/",
                "accept-encoding": "gzip",
                "accept-language": "en-US,en;q=0.9"
            }

            # Determine the appropriate driver based on the model
            driver = cls.get_driver_for_model(model)

            json_data = {
                "interface": "puter-image-generation" if model in cls.image_models else "puter-chat-completion",
                "driver": driver,
                "test_mode": messages[0]["content"] == "test",
                "method": "generate" if model in cls.image_models else "complete",
                "args": {"prompt": format_media_prompt(messages, prompt)} if model in cls.image_models else {
                    "messages": list(render_messages(messages, media)),
                    "model": model,
                    "stream": stream,
                    **{param: kwargs.get(param) for param in extra_parameters if param in kwargs}
                }
            }
            async with session.post(
                cls.api_endpoint, 
                headers=headers, 
                json=json_data,
                proxy=proxy
            ) as response:
                await raise_for_status(response)
                mime_type = response.headers.get("content-type", "")
                if mime_type.startswith("text/plain"):
                    yield await response.text()
                    return
                elif mime_type.startswith("text/event-stream"):
                    reasoning = False
                    async for result in sse_stream(response.content):
                        if "error" in result:
                            raise ResponseError(result["error"].get("message", result["error"]))
                        choices = result.get("choices", [{}])
                        choice = choices.pop() if choices else {}
                        content = choice.get("delta", {}).get("content")
                        reasoning_content = choice.get("delta", {}).get("reasoning_content")
                        if reasoning_content:
                            reasoning = True
                            yield Reasoning(reasoning_content)
                        elif content:
                            if reasoning:
                                yield Reasoning(status="")
                                reasoning = False
                            yield content
                        if result.get("usage") is not None:
                            yield Usage(**result["usage"])
                        tool_calls = choice.get("delta", {}).get("tool_calls")
                        if tool_calls:
                            yield ToolCalls(choice["delta"]["tool_calls"])
                        finish_reason = choice.get("finish_reason")
                        if finish_reason:
                            yield FinishReason(finish_reason)
                elif mime_type.startswith("application/json"):
                    result = await response.json()
                    if "choices" in result:
                        choice = result["choices"][0]
                    elif "result" in result:
                        choice = result.get("result", {})
                    else:
                        raise ResponseError(result)
                    message = choice.get("message", {})
                    reasoning_content = message.get("reasoning_content")
                    if reasoning_content:
                        yield Reasoning(reasoning_content)
                    content = message.get("content", "")
                    if isinstance(content, list):
                        for item in content:
                            if item.get("type") == "text":
                                yield item.get("text", "")
                    elif content:
                        yield content
                    if "tool_calls" in message:
                        yield ToolCalls(message["tool_calls"])
                    if result.get("usage") is not None:
                        yield Usage(**result["usage"])
                    finish_reason = choice.get("finish_reason")
                    if finish_reason:
                        yield FinishReason(finish_reason)
                elif mime_type.startswith("application/x-ndjson"):
                    async for line in response.content:
                        data = json.loads(line)
                        if data.get("type") == "text":
                            yield data.get("text", "")
                else:
                    raise ResponseError(f"Unexpected content type: {mime_type}")