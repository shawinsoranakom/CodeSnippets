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
        """Stream content generation from Antigravity API."""
        # Convert user-facing model name to internal API name
        if model in Antigravity.model_aliases:
            model = Antigravity.model_aliases[model]

        await self.auth_manager.initialize_auth()

        project_id = await self.discover_project_id()

        # Convert messages to Gemini format
        contents = self._messages_to_gemini_format(
            [m for m in messages if m["role"] not in ["developer", "system"]],
            media=kwargs.get("media", None)
        )
        system_prompt = get_system_prompt(messages)
        request_data = {}
        if system_prompt:
            request_data["system_instruction"] = {"parts": {"text": system_prompt}}

        # Convert OpenAI-style tools to Gemini format
        gemini_tools = None
        function_declarations = []
        if tools:
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

        # Build generation config
        generation_config = {
            "maxOutputTokens": max_tokens or 32000,  # Antigravity default
            "temperature": temperature,
            "topP": top_p,
            "stop": stop,
            "presencePenalty": presence_penalty,
            "frequencyPenalty": frequency_penalty,
            "seed": seed,
        }

        # Handle response format
        if response_format is not None and response_format.get("type") == "json_object":
            generation_config["responseMimeType"] = "application/json"

        # Handle thinking configuration
        if thinking_budget:
            generation_config["thinkingConfig"] = {
                "thinkingBudget": thinking_budget,
                "includeThoughts": True
            }

        # Compose request body with required Antigravity fields
        req_body = {
            "model": model,
            "project": project_id,
            "userAgent": "antigravity",
            "requestType": "agent",
            "requestId": f"req-{secrets.token_hex(8)}",
            "request": {
                "contents": contents,
                "generationConfig": generation_config,
                "tools": gemini_tools,
                **request_data
            },
        }

        # Add tool config if specified, only include allowedFunctionNames if mode is ANY
        if tool_choice and gemini_tools:
            mode = tool_choice.upper()
            function_calling_config = {"mode": mode}
            if mode == "ANY":
                function_calling_config["allowedFunctionNames"] = [fd["name"] for fd in function_declarations]
            req_body["request"]["toolConfig"] = {"functionCallingConfig": function_calling_config}

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
            **ANTIGRAVITY_HEADERS,
        }

        # Use production URL for streaming (most reliable)
        base_url = PRODUCTION_URL
        url = f"{base_url}:streamGenerateContent?alt=sse"

        # Streaming SSE parsing helper
        async def parse_sse_stream(stream: aiohttp.StreamReader) -> AsyncGenerator[Dict[str, Any], None]:
            """Parse SSE stream yielding parsed JSON objects."""
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
        connector = get_connector(None, proxy)

        async with ClientSession(headers=headers, timeout=timeout, connector=connector) as session:
            async with session.post(url, json=req_body) as resp:
                if not resp.ok:
                    if resp.status == 503:
                        try:
                            retry_delay = int(max([float(d.get("retryDelay", 0)) for d in (await resp.json(content_type=None)).get("error", {}).get("details", [])]))
                        except ValueError:
                            retry_delay = 30  # Default retry delay if not specified
                        debug.log(f"Received 503 error, retrying after {retry_delay}")
                        if retry_delay <= 120:
                            await asyncio.sleep(retry_delay)
                            resp = await session.post(url, json=req_body)
                            if not resp.ok:
                                debug.error(f"Retry after 503 failed with status {resp.status}")
                if not resp.ok:
                    if resp.status == 401:
                        raise MissingAuthError("Unauthorized (401) from Antigravity API")
                    error_body = await resp.text()
                    raise RuntimeError(f"Antigravity API error {resp.status}: {error_body}")

                usage_metadata = {}
                async for json_data in parse_sse_stream(resp.content):
                    # Process JSON data according to Gemini API structure
                    candidates = json_data.get("response", {}).get("candidates", [])
                    usage_metadata = json_data.get("response", {}).get("usageMetadata", usage_metadata)

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
                            async for media in save_response_media(part["inlineData"], format_media_prompt(messages)):
                                yield media

                        # File data (e.g. external image)
                        elif "fileData" in part:
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