async def llm_call(
    credentials: APIKeyCredentials,
    llm_model: LlmModel,
    prompt: list[dict],
    max_tokens: int | None,
    force_json_output: bool = False,
    tools: list[dict] | None = None,
    ollama_host: str = "localhost:11434",
    parallel_tool_calls=None,
    compress_prompt_to_fit: bool = True,
) -> LLMResponse:
    """
    Make a call to a language model.

    Args:
        credentials: The API key credentials to use.
        llm_model: The LLM model to use.
        prompt: The prompt to send to the LLM.
        force_json_output: Whether the response should be in JSON format.
        max_tokens: The maximum number of tokens to generate in the chat completion.
        tools: The tools to use in the chat completion.
        ollama_host: The host for ollama to use.

    Returns:
        LLMResponse object containing:
            - prompt: The prompt sent to the LLM.
            - response: The text response from the LLM.
            - tool_calls: Any tool calls the model made, if applicable.
            - prompt_tokens: The number of tokens used in the prompt.
            - completion_tokens: The number of tokens used in the completion.
    """
    provider = llm_model.metadata.provider
    context_window = llm_model.context_window

    # Transparent OpenRouter routing for Anthropic models: when an OpenRouter API key
    # is configured, route direct-Anthropic models through OpenRouter instead. This
    # gives us the x-total-cost header for free, so provider_cost is always populated
    # without manual token-rate arithmetic.
    or_key = settings.secrets.open_router_api_key
    or_model_id: str | None = None
    if provider == "anthropic" and or_key:
        provider = "open_router"
        credentials = APIKeyCredentials(
            provider=ProviderName.OPEN_ROUTER,
            title="OpenRouter (auto)",
            api_key=SecretStr(or_key),
        )
        or_model_id = f"anthropic/{llm_model.value}"

    if compress_prompt_to_fit:
        result = await compress_context(
            messages=prompt,
            target_tokens=llm_model.context_window // 2,
            client=None,  # Truncation-only, no LLM summarization
            reserve=0,  # Caller handles response token budget separately
        )
        if result.error:
            logger.warning(
                f"Prompt compression did not meet target: {result.error}. "
                f"Proceeding with {result.token_count} tokens."
            )
        prompt = result.messages

    # Sanitize unpaired surrogates in message content to prevent
    # UnicodeEncodeError when httpx encodes the JSON request body.
    for msg in prompt:
        content = msg.get("content")
        if isinstance(content, str):
            try:
                content.encode("utf-8")
            except UnicodeEncodeError:
                logger.warning("Sanitized unpaired surrogates in LLM prompt content")
                msg["content"] = content.encode("utf-8", errors="surrogatepass").decode(
                    "utf-8", errors="replace"
                )

    # Calculate available tokens based on context window and input length
    estimated_input_tokens = estimate_token_count(prompt)
    model_max_output = llm_model.max_output_tokens or int(2**15)
    user_max = max_tokens or model_max_output
    available_tokens = max(context_window - estimated_input_tokens, 0)
    max_tokens = max(min(available_tokens, model_max_output, user_max), 1)

    if provider == "openai":
        oai_client = openai.AsyncOpenAI(api_key=credentials.api_key.get_secret_value())

        tools_param = convert_tools_to_responses_format(tools) if tools else openai.omit

        text_config = openai.omit
        if force_json_output:
            text_config = {"format": {"type": "json_object"}}  # type: ignore

        response = await oai_client.responses.create(
            model=llm_model.value,
            input=prompt,  # type: ignore[arg-type]
            tools=tools_param,  # type: ignore[arg-type]
            max_output_tokens=max_tokens,
            parallel_tool_calls=get_parallel_tool_calls_param(
                llm_model, parallel_tool_calls
            ),
            text=text_config,  # type: ignore[arg-type]
            store=False,
        )

        raw_tool_calls = extract_responses_tool_calls(response)
        tool_calls = (
            [
                ToolContentBlock(
                    id=tc["id"],
                    type=tc["type"],
                    function=ToolCall(
                        name=tc["function"]["name"],
                        arguments=tc["function"]["arguments"],
                    ),
                )
                for tc in raw_tool_calls
            ]
            if raw_tool_calls
            else None
        )
        reasoning = extract_responses_reasoning(response)
        content = extract_responses_content(response)
        prompt_tokens, completion_tokens = extract_responses_usage(response)

        return LLMResponse(
            raw_response=response,
            prompt=prompt,
            response=content,
            tool_calls=tool_calls,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            reasoning=reasoning,
        )
    elif provider == "anthropic":
        an_tools = convert_openai_tool_fmt_to_anthropic(tools)
        # Cache tool definitions alongside the system prompt.
        # Placing cache_control on the last tool caches all tool schemas as a
        # single prefix — reads cost 10% of normal input tokens.
        if isinstance(an_tools, list) and an_tools:
            an_tools[-1] = {**an_tools[-1], "cache_control": {"type": "ephemeral"}}

        system_messages = [p["content"] for p in prompt if p["role"] == "system"]
        sysprompt = " ".join(system_messages)

        messages = []
        last_role = None
        for p in prompt:
            if p["role"] in ["user", "assistant"]:
                if (
                    p["role"] == last_role
                    and isinstance(messages[-1]["content"], str)
                    and isinstance(p["content"], str)
                ):
                    # If the role is the same as the last one, combine the content
                    messages[-1]["content"] += p["content"]
                else:
                    messages.append({"role": p["role"], "content": p["content"]})
                    last_role = p["role"]

        client = anthropic.AsyncAnthropic(
            api_key=credentials.api_key.get_secret_value()
        )
        # create_kwargs is built as a plain dict so we can conditionally add
        # the `system` field only when the prompt is non-empty.  Anthropic's
        # API rejects empty text blocks (returns HTTP 400), so omitting the
        # field is the correct behaviour for whitespace-only prompts.
        create_kwargs: dict[str, Any] = dict(
            model=llm_model.value,
            messages=messages,
            max_tokens=max_tokens,
            # `an_tools` may be anthropic.NOT_GIVEN when no tools were
            # configured. The SDK treats NOT_GIVEN as a sentinel meaning "omit
            # this field from the serialized request", so passing it here is
            # equivalent to not including the key at all — no `tools` field is
            # sent to the API in that case.
            tools=an_tools,
            timeout=600,
        )
        if sysprompt.strip():
            # Wrap the system prompt in a single cacheable text block.
            # The guard intentionally omits `system` for whitespace-only
            # prompts — Anthropic rejects empty text blocks with HTTP 400.
            create_kwargs["system"] = [
                {
                    "type": "text",
                    "text": sysprompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ]
        resp = await client.messages.create(**create_kwargs)

        if not resp.content:
            raise ValueError("No content returned from Anthropic.")

        tool_calls = None
        for content_block in resp.content:
            # Antropic is different to openai, need to iterate through
            # the content blocks to find the tool calls
            if content_block.type == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append(
                    ToolContentBlock(
                        id=content_block.id,
                        type=content_block.type,
                        function=ToolCall(
                            name=content_block.name,
                            arguments=json.dumps(content_block.input),
                        ),
                    )
                )

        if not tool_calls and resp.stop_reason == "tool_use":
            logger.warning(
                f"Tool use stop reason but no tool calls found in content. {resp}"
            )

        reasoning = None
        for content_block in resp.content:
            if hasattr(content_block, "type") and content_block.type == "thinking":
                reasoning = content_block.thinking
                break

        return LLMResponse(
            raw_response=resp,
            prompt=prompt,
            response=(
                resp.content[0].name
                if isinstance(resp.content[0], anthropic.types.ToolUseBlock)
                else getattr(resp.content[0], "text", "")
            ),
            tool_calls=tool_calls,
            prompt_tokens=resp.usage.input_tokens,
            completion_tokens=resp.usage.output_tokens,
            cache_read_tokens=getattr(resp.usage, "cache_read_input_tokens", None) or 0,
            cache_creation_tokens=getattr(
                resp.usage, "cache_creation_input_tokens", None
            )
            or 0,
            reasoning=reasoning,
        )
    elif provider == "groq":
        if tools:
            raise ValueError("Groq does not support tools.")

        client = AsyncGroq(api_key=credentials.api_key.get_secret_value())
        response_format = {"type": "json_object"} if force_json_output else None
        response = await client.chat.completions.create(
            model=llm_model.value,
            messages=prompt,  # type: ignore
            response_format=response_format,  # type: ignore
            max_tokens=max_tokens,
        )
        if not response.choices:
            raise ValueError("Groq returned empty choices in response")
        return LLMResponse(
            raw_response=response.choices[0].message,
            prompt=prompt,
            response=response.choices[0].message.content or "",
            tool_calls=None,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            reasoning=None,
        )
    elif provider == "ollama":
        if tools:
            raise ValueError("Ollama does not support tools.")

        # Validate user-provided Ollama host to prevent SSRF etc.
        await validate_url_host(
            ollama_host, trusted_hostnames=[settings.config.ollama_host]
        )

        client = ollama.AsyncClient(host=ollama_host)
        sys_messages = [p["content"] for p in prompt if p["role"] == "system"]
        usr_messages = [p["content"] for p in prompt if p["role"] != "system"]
        response = await client.generate(
            model=llm_model.value,
            prompt=f"{sys_messages}\n\n{usr_messages}",
            stream=False,
            options={"num_ctx": max_tokens},
        )
        return LLMResponse(
            raw_response=response.get("response") or "",
            prompt=prompt,
            response=response.get("response") or "",
            tool_calls=None,
            prompt_tokens=response.get("prompt_eval_count") or 0,
            completion_tokens=response.get("eval_count") or 0,
            reasoning=None,
        )
    elif provider == "open_router":
        tools_param = tools if tools else openai.NOT_GIVEN
        client = openai.AsyncOpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=credentials.api_key.get_secret_value(),
        )

        parallel_tool_calls_param = get_parallel_tool_calls_param(
            llm_model, parallel_tool_calls
        )

        response = await client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://agpt.co",
                "X-Title": "AutoGPT",
            },
            model=or_model_id or llm_model.value,
            messages=prompt,  # type: ignore
            max_tokens=max_tokens,
            tools=tools_param,  # type: ignore
            parallel_tool_calls=parallel_tool_calls_param,
        )

        if not response.choices:
            raise ValueError(f"OpenRouter returned empty choices: {response}")

        tool_calls = extract_openai_tool_calls(response)
        reasoning = extract_openai_reasoning(response)

        return LLMResponse(
            raw_response=response.choices[0].message,
            prompt=prompt,
            response=response.choices[0].message.content or "",
            tool_calls=tool_calls,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            reasoning=reasoning,
            provider_cost=extract_openrouter_cost(response),
        )
    elif provider == "llama_api":
        tools_param = tools if tools else openai.NOT_GIVEN
        client = openai.AsyncOpenAI(
            base_url="https://api.llama.com/compat/v1/",
            api_key=credentials.api_key.get_secret_value(),
        )

        parallel_tool_calls_param = get_parallel_tool_calls_param(
            llm_model, parallel_tool_calls
        )

        response = await client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://agpt.co",
                "X-Title": "AutoGPT",
            },
            model=llm_model.value,
            messages=prompt,  # type: ignore
            max_tokens=max_tokens,
            tools=tools_param,  # type: ignore
            parallel_tool_calls=parallel_tool_calls_param,
        )

        if not response.choices:
            raise ValueError(f"Llama API returned empty choices: {response}")

        tool_calls = extract_openai_tool_calls(response)
        reasoning = extract_openai_reasoning(response)

        return LLMResponse(
            raw_response=response.choices[0].message,
            prompt=prompt,
            response=response.choices[0].message.content or "",
            tool_calls=tool_calls,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            reasoning=reasoning,
        )
    elif provider == "aiml_api":
        client = openai.OpenAI(
            base_url="https://api.aimlapi.com/v2",
            api_key=credentials.api_key.get_secret_value(),
            default_headers={
                "X-Project": "AutoGPT",
                "X-Title": "AutoGPT",
                "HTTP-Referer": "https://github.com/Significant-Gravitas/AutoGPT",
            },
        )

        completion = client.chat.completions.create(
            model=llm_model.value,
            messages=prompt,  # type: ignore
            max_tokens=max_tokens,
        )
        if not completion.choices:
            raise ValueError("AI/ML API returned empty choices in response")

        return LLMResponse(
            raw_response=completion.choices[0].message,
            prompt=prompt,
            response=completion.choices[0].message.content or "",
            tool_calls=None,
            prompt_tokens=completion.usage.prompt_tokens if completion.usage else 0,
            completion_tokens=(
                completion.usage.completion_tokens if completion.usage else 0
            ),
            reasoning=None,
        )
    elif provider == "v0":
        tools_param = tools if tools else openai.NOT_GIVEN
        client = openai.AsyncOpenAI(
            base_url="https://api.v0.dev/v1",
            api_key=credentials.api_key.get_secret_value(),
        )

        response_format = None
        if force_json_output:
            response_format = {"type": "json_object"}

        parallel_tool_calls_param = get_parallel_tool_calls_param(
            llm_model, parallel_tool_calls
        )

        response = await client.chat.completions.create(
            model=llm_model.value,
            messages=prompt,  # type: ignore
            response_format=response_format,  # type: ignore
            max_tokens=max_tokens,
            tools=tools_param,  # type: ignore
            parallel_tool_calls=parallel_tool_calls_param,
        )

        if not response.choices:
            raise ValueError(f"v0 API returned empty choices: {response}")

        tool_calls = extract_openai_tool_calls(response)
        reasoning = extract_openai_reasoning(response)

        return LLMResponse(
            raw_response=response.choices[0].message,
            prompt=prompt,
            response=response.choices[0].message.content or "",
            tool_calls=tool_calls,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            reasoning=reasoning,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")