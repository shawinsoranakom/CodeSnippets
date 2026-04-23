async def async_iter_run_tools(
    provider: ProviderType,
    model: str,
    messages: Messages,
    tool_calls: Optional[List[dict]] = None,
    **kwargs,
) -> AsyncIterator:
    """Asynchronously run tools and yield results"""

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
        async for chunk in ToolSupportProvider.create_async_generator(
            model=model,
            messages=messages,
            stream=stream,
            media=kwargs.get("media"),
            tools=tools,
            tool_choice=tool_choice,
            provider=provider,
            **emu_kwargs,
        ):
            yield chunk
        return

    # Process web search
    sources = None
    web_search = kwargs.get("web_search")
    if web_search:
        debug.log(f"Performing web search with value: {web_search}")
        messages, sources = await perform_web_search(messages, web_search)

    # Get API key
    if not kwargs.get("api_key") or AppConfig.disable_custom_api_key:
        api_key = AuthManager.load_api_key(provider)
        if api_key:
            kwargs["api_key"] = api_key

    # Process tool calls
    if tool_calls:
        messages, sources, extra_kwargs = await ToolHandler.process_tools(
            messages, tool_calls, provider
        )
        kwargs.update(extra_kwargs)

    # Generate response
    method = get_async_provider_method(provider)
    response = method(model=model, messages=messages, **kwargs)
    timeout = kwargs.get("stream_timeout") if provider.use_stream_timeout else kwargs.get("timeout")
    response = wait_for(response, timeout=timeout) if stream else response

    try:
        usage_model = model
        usage_provider = provider.__name__
        completion_tokens = 0
        usage = None
        async for chunk in response:
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
            yield chunk
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
        if has_aiofile:
            async with async_open(usage_file, "a") as f:
                asyncio.create_task(f.write(f"{json.dumps(usage)}\n"))
        else:
            with usage_file.open("a") as f:
                f.write(f"{json.dumps(usage)}\n")
        if completion_tokens > 0:
            provider.live += 1
    except Exception:
        provider.live -= 1
        raise

    # Yield sources if available
    if sources is not None:
        yield sources