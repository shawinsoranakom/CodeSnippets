def build_app(
    args: Namespace,
    supported_tasks: tuple["SupportedTask", ...] | None = None,
    model_config: ModelConfig | None = None,
) -> FastAPI:
    if supported_tasks is None:
        warnings.warn(
            "The 'supported_tasks' parameter was not provided to "
            "build_app and will be required in a future version. "
            "Defaulting to ('generate',).",
            DeprecationWarning,
            stacklevel=2,
        )
        supported_tasks = _FALLBACK_SUPPORTED_TASKS

    if args.disable_fastapi_docs:
        app = FastAPI(
            openapi_url=None, docs_url=None, redoc_url=None, lifespan=lifespan
        )
    elif args.enable_offline_docs:
        app = FastAPI(docs_url=None, redoc_url=None, lifespan=lifespan)
    else:
        app = FastAPI(lifespan=lifespan)
    app.state.args = args

    from vllm.entrypoints.serve import register_vllm_serve_api_routers

    register_vllm_serve_api_routers(app)

    from vllm.entrypoints.openai.models.api_router import (
        attach_router as register_models_api_router,
    )

    register_models_api_router(app)

    from vllm.entrypoints.sagemaker.api_router import (
        attach_router as register_sagemaker_api_router,
    )

    register_sagemaker_api_router(app, supported_tasks, model_config)

    if "generate" in supported_tasks:
        from vllm.entrypoints.openai.generate.api_router import (
            register_generate_api_routers,
        )

        register_generate_api_routers(app)

        from vllm.entrypoints.serve.disagg.api_router import (
            attach_router as attach_disagg_router,
        )

        attach_disagg_router(app)

        from vllm.entrypoints.serve.rlhf.api_router import (
            attach_router as attach_rlhf_router,
        )

        attach_rlhf_router(app)

        from vllm.entrypoints.serve.elastic_ep.api_router import (
            attach_router as elastic_ep_attach_router,
        )

        elastic_ep_attach_router(app)

        from vllm.entrypoints.openai.generative_scoring.api_router import (
            register_generative_scoring_api_router,
        )

        register_generative_scoring_api_router(app)

    if "generate" in supported_tasks or "render" in supported_tasks:
        from vllm.entrypoints.serve.render.api_router import (
            attach_router as attach_render_router,
        )

        attach_render_router(app)

    if "transcription" in supported_tasks:
        from vllm.entrypoints.openai.speech_to_text.api_router import (
            attach_router as register_speech_to_text_api_router,
        )

        register_speech_to_text_api_router(app)

    if "realtime" in supported_tasks:
        from vllm.entrypoints.openai.realtime.api_router import (
            attach_router as register_realtime_api_router,
        )

        register_realtime_api_router(app)

    if any(task in POOLING_TASKS for task in supported_tasks):
        from vllm.entrypoints.pooling.factories import register_pooling_api_routers

        register_pooling_api_routers(app, supported_tasks, model_config)

    app.root_path = args.root_path
    app.add_middleware(
        CORSMiddleware,
        allow_origins=args.allowed_origins,
        allow_credentials=args.allow_credentials,
        allow_methods=args.allowed_methods,
        allow_headers=args.allowed_headers,
    )

    app.exception_handler(HTTPException)(http_exception_handler)
    app.exception_handler(RequestValidationError)(validation_exception_handler)
    app.exception_handler(EngineGenerateError)(engine_error_handler)
    app.exception_handler(EngineDeadError)(engine_error_handler)
    app.exception_handler(GenerationError)(generation_error_handler)
    app.exception_handler(Exception)(exception_handler)

    # Ensure --api-key option from CLI takes precedence over VLLM_API_KEY
    if tokens := [key for key in (args.api_key or [envs.VLLM_API_KEY]) if key]:
        from vllm.entrypoints.openai.server_utils import AuthenticationMiddleware

        app.add_middleware(AuthenticationMiddleware, tokens=tokens)

    if args.enable_request_id_headers:
        from vllm.entrypoints.openai.server_utils import XRequestIdMiddleware

        app.add_middleware(XRequestIdMiddleware)

    # Add scaling middleware to check for scaling state
    app.add_middleware(ScalingMiddleware)

    if "realtime" in supported_tasks:
        # Add WebSocket metrics middleware
        from vllm.entrypoints.openai.realtime.metrics import (
            WebSocketMetricsMiddleware,
        )

        app.add_middleware(WebSocketMetricsMiddleware)

    if envs.VLLM_DEBUG_LOG_API_SERVER_RESPONSE:
        logger.warning(
            "CAUTION: Enabling log response in the API Server. "
            "This can include sensitive information and should be "
            "avoided in production."
        )
        app.middleware("http")(log_response)

    for middleware in args.middleware:
        module_path, object_name = middleware.rsplit(".", 1)
        imported = getattr(importlib.import_module(module_path), object_name)
        if inspect.isclass(imported):
            app.add_middleware(imported)  # type: ignore[arg-type]
        elif inspect.iscoroutinefunction(imported):
            app.middleware("http")(imported)
        else:
            raise ValueError(
                f"Invalid middleware {middleware}. Must be a function or a class."
            )

    app = sagemaker_standards_bootstrap(app)
    return app