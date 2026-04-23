async def init_app_state(
    engine_client: EngineClient,
    state: State,
    args: Namespace,
    supported_tasks: tuple["SupportedTask", ...] | None = None,
) -> None:
    vllm_config = engine_client.vllm_config
    if supported_tasks is None:
        warnings.warn(
            "The 'supported_tasks' parameter was not provided to "
            "init_app_state and will be required in a future version. "
            "Please pass 'supported_tasks' explicitly.",
            DeprecationWarning,
            stacklevel=2,
        )
        supported_tasks = _FALLBACK_SUPPORTED_TASKS

    if args.served_model_name is not None:
        served_model_names = args.served_model_name
    else:
        served_model_names = [args.model]

    if args.enable_log_requests:
        request_logger = RequestLogger(max_log_len=args.max_log_len)
    else:
        request_logger = None

    base_model_paths = [
        BaseModelPath(name=name, model_path=args.model) for name in served_model_names
    ]

    state.engine_client = engine_client
    state.log_stats = not args.disable_log_stats
    state.vllm_config = vllm_config
    state.args = args
    resolved_chat_template = load_chat_template(args.chat_template)

    # Merge default_mm_loras into the static lora_modules
    default_mm_loras = (
        vllm_config.lora_config.default_mm_loras
        if vllm_config.lora_config is not None
        else {}
    )
    lora_modules = process_lora_modules(args.lora_modules, default_mm_loras)

    state.openai_serving_models = OpenAIServingModels(
        engine_client=engine_client,
        base_model_paths=base_model_paths,
        lora_modules=lora_modules,
    )
    await state.openai_serving_models.init_static_loras()

    state.openai_serving_render = OpenAIServingRender(
        model_config=engine_client.model_config,
        renderer=engine_client.renderer,
        model_registry=state.openai_serving_models.registry,
        request_logger=request_logger,
        chat_template=resolved_chat_template,
        chat_template_content_format=args.chat_template_content_format,
        trust_request_chat_template=args.trust_request_chat_template,
        enable_auto_tools=args.enable_auto_tool_choice,
        exclude_tools_when_tool_choice_none=args.exclude_tools_when_tool_choice_none,
        tool_parser=args.tool_call_parser,
        reasoning_parser=args.structured_outputs_config.reasoning_parser,
        default_chat_template_kwargs=args.default_chat_template_kwargs,
        log_error_stack=args.log_error_stack,
    )

    state.openai_serving_tokenization = OpenAIServingTokenization(
        engine_client,
        state.openai_serving_models,
        state.openai_serving_render,
        request_logger=request_logger,
        chat_template=resolved_chat_template,
        chat_template_content_format=args.chat_template_content_format,
        default_chat_template_kwargs=args.default_chat_template_kwargs,
        trust_request_chat_template=args.trust_request_chat_template,
    )

    if "generate" in supported_tasks:
        from vllm.entrypoints.openai.generate.api_router import init_generate_state

        await init_generate_state(
            engine_client, state, args, request_logger, supported_tasks
        )

        from vllm.entrypoints.openai.generative_scoring.api_router import (
            init_generative_scoring_state,
        )

        await init_generative_scoring_state(engine_client, state, args, request_logger)

    if "transcription" in supported_tasks:
        from vllm.entrypoints.openai.speech_to_text.api_router import (
            init_transcription_state,
        )

        init_transcription_state(
            engine_client, state, args, request_logger, supported_tasks
        )

    if "realtime" in supported_tasks:
        from vllm.entrypoints.openai.realtime.api_router import init_realtime_state

        init_realtime_state(engine_client, state, args, request_logger, supported_tasks)

    if any(task in POOLING_TASKS for task in supported_tasks):
        from vllm.entrypoints.pooling.factories import init_pooling_state

        init_pooling_state(engine_client, state, args, request_logger, supported_tasks)

    state.enable_server_load_tracking = args.enable_server_load_tracking
    state.server_load_metrics = 0