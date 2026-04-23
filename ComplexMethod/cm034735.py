async def stream_content(
        self,
        model: str,
        messages: Messages,
        *,
        proxy: Optional[str] = None,
        thinking_budget: Optional[int] = None,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncGenerator:
        await self.auth_manager.initialize_auth()

        project_id = await self.discover_project_id()

        # Convert messages to Gemini format
        contents = self._messages_to_gemini_format([m for m in messages if m["role"] not in ["developer", "system"]], media=kwargs.get("media", None))
        system_prompt = get_system_prompt(messages)
        requestData = {}
        if system_prompt:
            requestData["system_instruction"] = {"parts": {"text": system_prompt}}

        # Convert OpenAI-style tools to Gemini format
        gemini_tools = None
        if tools:
            function_declarations = []
            for tool in tools:
                if tool.get("type") == "function" and "function" in tool:
                    func = tool["function"]
                    function_declarations.append({
                        "name": func.get("name"),
                        "description": func.get("description", ""),
                        "parameters": _sanitize_schema(func.get("parameters", {}))
                    })
            if function_declarations:
                gemini_tools = [{"functionDeclarations": function_declarations}]

        # Compose request body
        # Build toolConfig with allowedFunctionNames only if mode is ANY
        tool_config = None
        if tool_choice and gemini_tools:
            mode = tool_choice.upper()
            function_calling_config = {"mode": mode}
            if mode == "ANY":
                function_calling_config["allowedFunctionNames"] = [fd["name"] for fd in function_declarations]
            tool_config = {"functionCallingConfig": function_calling_config}

        req_body = {
            "model": model,
            "project": project_id,
            "request": {
                "contents": contents,
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": temperature,
                    "topP": top_p,
                    "stop": stop,
                    "presencePenalty": presence_penalty,
                    "frequencyPenalty": frequency_penalty,
                    "seed": seed,
                    "responseMimeType": None if response_format is None else ("application/json" if response_format.get("type") == "json_object" else None),
                    "thinkingConfig": {
                        "thinkingBudget": thinking_budget,
                        "includeThoughts": True
                    } if thinking_budget else None,
                },
                "tools": gemini_tools,
                "toolConfig": tool_config,
                **requestData
            },
        }

        # Remove None values recursively
        def clean_none(d):
            if isinstance(d, dict):
                return {k: clean_none(v) for k, v in d.items() if v is not None}
            if isinstance(d, list):
                return [clean_none(x) for x in d if x is not None]
            return d

        req_body = clean_none(req_body)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_manager.get_access_token()}",
        }

        url = f"{self.base_url}:streamGenerateContent?alt=sse"

        # Streaming SSE parsing helper
        async def parse_sse_stream(stream: aiohttp.StreamReader) -> AsyncGenerator[Dict[str, Any], None]:
            """Parse SSE stream yielding parsed JSON objects"""
            buffer = ""
            object_buffer = ""

            async for chunk_bytes in stream.iter_any():
                chunk = chunk_bytes.decode()
                buffer += chunk
                lines = buffer.split("\n")
                buffer = lines.pop()  # Save last incomplete line back

                for line in lines:
                    line = line.strip()
                    if line == "":
                        # Empty line indicates end of SSE message -> parse object buffer
                        if object_buffer:
                            try:
                                yield json.loads(object_buffer)
                            except Exception as e:
                                debug.error(f"Error parsing SSE JSON: {e}")
                            object_buffer = ""
                    elif line.startswith("data: "):
                        object_buffer += line[6:]

            # Final parse when stream ends
            if object_buffer:
                try:
                    yield json.loads(object_buffer)
                except Exception as e:
                    debug.error(f"Error parsing final SSE JSON: {e}")

        timeout = ClientTimeout(total=None)  # No total timeout
        connector = get_connector(None, proxy)  # Customize connector as needed (supports proxy)

        async with ClientSession(headers=headers, timeout=timeout, connector=connector) as session:
            async with session.post(url, json=req_body) as resp:
                if not resp.ok:
                    if resp.status == 401:
                        # Possibly token expired: try login retry logic, omitted here for brevity
                        raise MissingAuthError(f"Unauthorized (401) from Gemini API")
                    error_body = await resp.text()
                    raise RuntimeError(f"Gemini API error {resp.status}: {error_body}")

                async for json_data in parse_sse_stream(resp.content):
                    # Process JSON data according to Gemini API structure
                    candidates = json_data.get("response", {}).get("candidates", [])
                    usage_metadata = json_data.get("response", {}).get("usageMetadata", {})

                    if not candidates:
                        continue

                    candidate = candidates[0]
                    content = candidate.get("content", {})
                    parts = content.get("parts", [])

                    tool_calls = []

                    for part in parts:
                        # Real thinking chunks
                        if part.get("thought") is True and "text" in part:
                            yield Reasoning(part["text"])

                        # Function calls from Gemini
                        elif "functionCall" in part:
                            tool_calls.append(part)

                        # Text content
                        elif "text" in part:
                            yield part["text"]

                        # Inline media data
                        elif "inlineData" in part:
                            # Media chunk - yield media asynchronously
                            async for media in save_response_media(part["inlineData"], format_media_prompt(messages)):
                                yield media

                        # File data (e.g. external image)
                        elif "fileData" in part:
                            # Just yield the file URI for now
                            file_data = part["fileData"]
                            yield ImageResponse(file_data.get("fileUri"))

                    if tool_calls:
                        # Convert Gemini tool calls to OpenAI format
                        openai_tool_calls = []
                        for i, part in enumerate(tool_calls):
                            tc = part["functionCall"]
                            tool_call_obj = {
                                "id": f"call_{i}_{tc.get('name', 'unknown')}",
                                "type": "function",
                                "function": {
                                    "name": tc.get("name"),
                                    "arguments": json.dumps(tc.get("args", {}))
                                }
                            }
                            # Preserve thought_signature for thinking models (Gemini 2.5+)
                            if "thoughtSignature" in part:
                                tool_call_obj["extra_content"] = {
                                    "google": {
                                        "thought_signature": part["thoughtSignature"]
                                    }
                                }
                            openai_tool_calls.append(tool_call_obj)
                        yield ToolCalls(openai_tool_calls)
                if usage_metadata:
                    yield Usage(**usage_metadata)