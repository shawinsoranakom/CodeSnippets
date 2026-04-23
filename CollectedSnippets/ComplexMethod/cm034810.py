def iter_run_tools(
    provider: ProviderType,
    model: str,
    messages: Messages,
    tool_calls: Optional[List[dict]] = None,
    **kwargs,
) -> Iterator:
    """Run tools synchronously and yield results"""

    tool_emulation = kwargs.pop("tool_emulation", None)
    if tool_emulation is None:
        tool_emulation = os.environ.get("G4F_TOOL_EMULATION", "").strip().lower() in (
            "1",
            "true",
            "yes",
        )

    stream = bool(kwargs.get("stream"))
    tools = kwargs.get("tools")
    if tool_emulation and tools and not tool_calls:
        from ..providers.tool_support import ToolSupportProvider

        emu_kwargs = dict(kwargs)
        emu_kwargs.pop("tools", None)
        tool_choice = emu_kwargs.pop("tool_choice", None)
        emu_kwargs.pop("parallel_tool_calls", None)
        emu_kwargs.pop("stream", None)
        emu_kwargs.pop("stream_timeout", None)
        yield from to_sync_generator(
            ToolSupportProvider.create_async_generator(
                model=model,
                messages=messages,
                stream=stream,
                media=kwargs.get("media"),
                tools=tools,
                tool_choice=tool_choice,
                provider=provider,
                **emu_kwargs,
            ),
            stream=stream,
        )
        return
    # Process web search
    web_search = kwargs.get("web_search")
    sources = None

    if web_search:
        debug.log(f"Performing web search with value: {web_search}")
        try:
            messages = messages.copy()
            search_query = (
                web_search
                if isinstance(web_search, str) and web_search != "true"
                else None
            )
            # Note: Using asyncio.run inside sync function is not ideal, but maintaining original pattern
            messages[-1]["content"], sources = asyncio.run(
                do_search(messages[-1]["content"], search_query)
            )
        except Exception as e:
            debug.error(f"Couldn't do web search:", e)

    # Get API key if needed
    if not kwargs.get("api_key") or AppConfig.disable_custom_api_key:
        api_key = AuthManager.load_api_key(provider)
        if api_key:
            kwargs["api_key"] = api_key

    # Process tool calls
    if tool_calls:
        for tool in tool_calls:
            if tool.get("type") == "function":
                function_name = tool.get("function", {}).get("name")
                debug.log(f"Processing tool call: {function_name}")
                if function_name == TOOL_NAMES["SEARCH"]:
                    tool["function"]["arguments"] = ToolHandler.validate_arguments(
                        tool["function"]
                    )
                    messages[-1]["content"] = get_search_message(
                        messages[-1]["content"],
                        raise_search_exceptions=True,
                        **tool["function"]["arguments"],
                    )
                elif function_name == TOOL_NAMES["CONTINUE"]:
                    if provider.__name__ not in ("OpenaiAccount", "HuggingFace"):
                        last_line = messages[-1]["content"].strip().splitlines()[-1]
                        content = f"Carry on from this point:\n{last_line}"
                        messages.append({"role": "user", "content": content})
                    else:
                        # Enable provider native continue
                        kwargs["action"] = "continue"
                elif function_name == TOOL_NAMES["BUCKET"]:

                    def on_bucket(match):
                        return "".join(read_bucket(get_bucket_dir(match.group(1))))

                    has_bucket = False
                    for message in messages:
                        if "content" in message and isinstance(message["content"], str):
                            new_message_content = re.sub(
                                r'{"bucket_id":"([^"]*)"}',
                                on_bucket,
                                message["content"],
                            )
                            if new_message_content != message["content"]:
                                has_bucket = True
                                message["content"] = new_message_content
                    last_message = messages[-1]["content"]
                    if has_bucket and isinstance(last_message, str):
                        if "\nSource: " in last_message:
                            messages[-1]["content"] = last_message + BUCKET_INSTRUCTIONS

    # Process response chunks
    try:
        thinking_start_time = 0
        processor = ThinkingProcessor()
        usage_model = model
        usage_provider = provider.__name__
        completion_tokens = 0
        usage = None
        method = get_provider_method(provider)
        for chunk in method(
            model=model, messages=messages, provider=provider, **kwargs
        ):
            if isinstance(chunk, FinishReason):
                if sources is not None:
                    yield sources
                    sources = None
                yield chunk
                continue
            elif isinstance(chunk, Sources):
                sources = None
            elif isinstance(chunk, str):
                completion_tokens += round(len(chunk.encode("utf-8")) / 4)
            elif isinstance(chunk, ProviderInfo):
                usage_model = getattr(chunk, "model", usage_model)
                usage_provider = getattr(chunk, "name", usage_provider)
            elif isinstance(chunk, Usage):
                usage = chunk
            if not isinstance(chunk, str):
                yield chunk
                continue

            thinking_start_time, results = processor.process_thinking_chunk(
                chunk, thinking_start_time
            )
            for result in results:
                yield result
        if usage is None:
            usage = get_usage(messages, completion_tokens)
            yield usage
        usage = {
            "user": kwargs.get("user"),
            "model": usage_model,
            "provider": usage_provider,
            **usage.get_dict(),
        }
        usage_dir = Path(get_cookies_dir()) / ".usage"
        usage_file = usage_dir / f"{datetime.date.today()}.jsonl"
        usage_dir.mkdir(parents=True, exist_ok=True)
        with usage_file.open("a") as f:
            f.write(f"{json.dumps(usage)}\n")
        if completion_tokens > 0:
            provider.live += 1
    except Exception:
        provider.live -= 1
        raise

    if sources is not None:
        yield sources