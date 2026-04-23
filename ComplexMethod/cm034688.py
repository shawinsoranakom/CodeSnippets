async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        proxy: str = None,
        timeout: int = 120,
        media: MediaListType = None,
        api_key: str = None,
        temperature: float = None,
        max_tokens: int = 4096,
        top_k: int = None,
        top_p: float = None,
        stop: list[str] = None,
        stream: bool = False,
        headers: dict = None,
        impersonate: str = None,
        tools: Optional[list] = None,
        beta_headers: Optional[list] = None,
        extra_body: dict = {},
        **kwargs
    ) -> AsyncResult:
        if api_key is None:
            raise MissingAuthError('Add a "api_key"')

        # Handle image inputs
        if media is not None:
            insert_images = []
            for image, _ in media:
                data = to_bytes(image)
                insert_images.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": is_accepted_format(data),
                        "data": base64.b64encode(data).decode(),
                    }
                })
            messages[-1]["content"] = [
                *insert_images,
                {
                    "type": "text",
                    "text": messages[-1]["content"]
                }
            ]

        # Extract system messages
        system = "\n".join([message["content"] for message in messages if message.get("role") == "system"])
        if system:
            messages = [message for message in messages if message.get("role") != "system"]
        else:
            system = None

        # Get model name
        model_name = cls.get_model(model, api_key=api_key)

        # Special handling for Opus 4.1 parameters<!--citation:6-->
        if "opus-4-1" in model_name:
            # Opus 4.1 doesn't allow both temperature and top_p
            if temperature is not None and top_p is not None:
                top_p = None  # Prefer temperature over top_p

        async with StreamSession(
            proxy=proxy,
            headers=cls.get_headers(stream, api_key, headers, beta_headers),
            timeout=timeout,
            impersonate=impersonate,
        ) as session:
            data = filter_none(
                messages=messages,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                top_k=top_k,
                top_p=top_p,
                stop_sequences=stop,
                system=system,
                stream=stream,
                tools=tools,
                **extra_body
            )
            async with session.post(f"{cls.base_url}/messages", json=data) as response:
                await raise_for_status(response)
                if not stream:
                    data = await response.json()
                    cls.raise_error(data)
                    tool_calls = []
                    if "type" in data and data["type"] == "message":
                        for content in data["content"]:
                            if content["type"] == "text":
                                yield content["text"]
                            elif content["type"] == "tool_use":
                                tool_calls.append({
                                    "id": content["id"],
                                    "type": "function",
                                    "function": { "name": content["name"], "arguments": json.dumps(content["input"]) }
                                })
                        if tool_calls:
                            yield ToolCalls(tool_calls)
                        if data.get("stop_reason") == "end_turn":
                            yield FinishReason("stop")
                        elif data.get("stop_reason") == "max_tokens":
                            yield FinishReason("length")
                        if "usage" in data:
                            yield Usage(**data["usage"])
                else:
                    content_block = None
                    partial_json = []
                    tool_calls = []
                    async for line in response.iter_lines():
                        if line.startswith(b"data: "):
                            chunk = line[6:]
                            if chunk == b"[DONE]":
                                break
                            data = json.loads(chunk)
                            cls.raise_error(data)
                            if "type" in data:
                                if data["type"] == "content_block_start":
                                    content_block = data["content_block"]
                                elif data["type"] == "content_block_delta":
                                    if content_block and content_block["type"] == "text":
                                        yield data["delta"]["text"]
                                    elif content_block and content_block["type"] == "tool_use":
                                        partial_json.append(data["delta"]["partial_json"])
                                elif data["type"] == "message_delta":
                                    if data["delta"].get("stop_reason") == "end_turn":
                                        yield FinishReason("stop")
                                    elif data["delta"].get("stop_reason") == "max_tokens":
                                        yield FinishReason("length")
                                    if "usage" in data:
                                        yield Usage(**data["usage"])
                                elif data["type"] == "content_block_stop":
                                    if content_block and content_block["type"] == "tool_use":
                                        tool_calls.append({
                                            "id": content_block["id"],
                                            "type": "function",
                                            "function": { 
                                                "name": content_block["name"], 
                                                "arguments": "".join(partial_json)
                                            }
                                        })
                                        partial_json = []
                                    content_block = None
                    if tool_calls:
                        yield ToolCalls(tool_calls)