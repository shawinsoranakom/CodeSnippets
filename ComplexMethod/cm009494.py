def _configure(
    callback_manager_cls: type[T],
    inheritable_callbacks: Callbacks = None,
    local_callbacks: Callbacks = None,
    inheritable_tags: list[str] | None = None,
    local_tags: list[str] | None = None,
    inheritable_metadata: dict[str, Any] | None = None,
    local_metadata: dict[str, Any] | None = None,
    *,
    verbose: bool = False,
    langsmith_inheritable_metadata: Mapping[str, Any] | None = None,
    langsmith_inheritable_tags: list[str] | None = None,
) -> T:
    """Configure the callback manager.

    Args:
        callback_manager_cls: The callback manager class.
        inheritable_callbacks: The inheritable callbacks.
        local_callbacks: The local callbacks.
        inheritable_tags: The inheritable tags.
        local_tags: The local tags.
        inheritable_metadata: The inheritable metadata.
        local_metadata: The local metadata.
        verbose: Whether to enable verbose mode.
        langsmith_inheritable_metadata: Default inheritable metadata applied to
            any `LangChainTracer` handlers via `set_defaults`.
        langsmith_inheritable_tags: Default inheritable tags applied to any
            `LangChainTracer` handlers via `set_defaults`.

    Raises:
        RuntimeError: If `LANGCHAIN_TRACING` is set but `LANGCHAIN_TRACING_V2` is not.

    Returns:
        The configured callback manager.
    """
    # Deferred to avoid importing langsmith at module level (~132ms).
    from langsmith.run_helpers import get_tracing_context  # noqa: PLC0415

    from langchain_core.tracers.context import (  # noqa: PLC0415
        _configure_hooks,
        _get_tracer_project,
        _tracing_v2_is_enabled,
        tracing_v2_callback_var,
    )
    from langchain_core.tracers.langchain import LangChainTracer  # noqa: PLC0415
    from langchain_core.tracers.stdout import ConsoleCallbackHandler  # noqa: PLC0415

    tracing_context = get_tracing_context()
    tracing_metadata = tracing_context["metadata"]
    tracing_tags = tracing_context["tags"]
    run_tree: Run | None = tracing_context["parent"]
    parent_run_id = None if run_tree is None else run_tree.id
    callback_manager = callback_manager_cls(
        handlers=[],
        parent_run_id=parent_run_id,
    )
    if inheritable_callbacks or local_callbacks:
        if isinstance(inheritable_callbacks, list) or inheritable_callbacks is None:
            inheritable_callbacks_ = inheritable_callbacks or []
            callback_manager = callback_manager_cls(
                handlers=inheritable_callbacks_.copy(),
                inheritable_handlers=inheritable_callbacks_.copy(),
                parent_run_id=parent_run_id,
            )
        else:
            parent_run_id_ = inheritable_callbacks.parent_run_id
            # Break ties between the external tracing context and inherited context
            if parent_run_id is not None and (
                parent_run_id_ is None
                # If the LC parent has already been reflected
                # in the run tree, we know the run_tree is either the
                # same parent or a child of the parent.
                or (run_tree and str(parent_run_id_) in run_tree.dotted_order)
            ):
                parent_run_id_ = parent_run_id
                # Otherwise, we assume the LC context has progressed
                # beyond the run tree and we should not inherit the parent.
            callback_manager = callback_manager_cls(
                handlers=inheritable_callbacks.handlers.copy(),
                inheritable_handlers=inheritable_callbacks.inheritable_handlers.copy(),
                parent_run_id=parent_run_id_,
                tags=inheritable_callbacks.tags.copy(),
                inheritable_tags=inheritable_callbacks.inheritable_tags.copy(),
                metadata=inheritable_callbacks.metadata.copy(),
                inheritable_metadata=inheritable_callbacks.inheritable_metadata.copy(),
            )
        local_handlers_ = (
            local_callbacks
            if isinstance(local_callbacks, list)
            else (local_callbacks.handlers if local_callbacks else [])
        )
        for handler in local_handlers_:
            callback_manager.add_handler(handler, inherit=False)
    if inheritable_tags or local_tags:
        callback_manager.add_tags(inheritable_tags or [])
        callback_manager.add_tags(local_tags or [], inherit=False)
    if inheritable_metadata or local_metadata:
        callback_manager.add_metadata(inheritable_metadata or {})
        callback_manager.add_metadata(local_metadata or {}, inherit=False)
    if tracing_tags:
        callback_manager.add_tags(tracing_tags.copy())

    v1_tracing_enabled_ = env_var_is_set("LANGCHAIN_TRACING") or env_var_is_set(
        "LANGCHAIN_HANDLER"
    )

    tracer_v2 = tracing_v2_callback_var.get()
    tracing_v2_enabled_ = _tracing_v2_is_enabled()

    if v1_tracing_enabled_ and not tracing_v2_enabled_:
        # if both are enabled, can silently ignore the v1 tracer
        msg = (
            "Tracing using LangChainTracerV1 is no longer supported. "
            "Please set the LANGCHAIN_TRACING_V2 environment variable to enable "
            "tracing instead."
        )
        raise RuntimeError(msg)

    tracer_project = _get_tracer_project()
    debug = _get_debug()
    if verbose or debug or tracing_v2_enabled_:
        if verbose and not any(
            isinstance(handler, StdOutCallbackHandler)
            for handler in callback_manager.handlers
        ):
            if debug:
                pass
            else:
                callback_manager.add_handler(StdOutCallbackHandler(), inherit=False)
        if debug and not any(
            isinstance(handler, ConsoleCallbackHandler)
            for handler in callback_manager.handlers
        ):
            callback_manager.add_handler(ConsoleCallbackHandler())
        if tracing_v2_enabled_ and not any(
            isinstance(handler, LangChainTracer)
            for handler in callback_manager.handlers
        ):
            if tracer_v2:
                callback_manager.add_handler(tracer_v2)
            else:
                try:
                    handler = LangChainTracer(
                        project_name=tracer_project,
                        client=(
                            run_tree.client
                            if run_tree is not None
                            else tracing_context["client"]
                        ),
                        tags=tracing_tags,
                        metadata=tracing_metadata,
                    )
                    callback_manager.add_handler(handler)
                except Exception as e:
                    logger.warning(
                        "Unable to load requested LangChainTracer."
                        " To disable this warning,"
                        " unset the LANGCHAIN_TRACING_V2 environment variables.\n"
                        "%s",
                        repr(e),
                    )
        if run_tree is not None:
            for handler in callback_manager.handlers:
                if isinstance(handler, LangChainTracer):
                    handler.order_map[run_tree.id] = (
                        run_tree.trace_id,
                        run_tree.dotted_order,
                    )
                    run_id_str = str(run_tree.id)
                    if run_id_str not in handler.run_map:
                        handler.run_map[run_id_str] = run_tree
                        handler._external_run_ids.setdefault(  # noqa: SLF001
                            run_id_str, 0
                        )
    for var, inheritable, handler_class, env_var in _configure_hooks:
        create_one = (
            env_var is not None
            and env_var_is_set(env_var)
            and handler_class is not None
        )
        if var.get() is not None or create_one:
            var_handler = (
                var.get() or cast("type[BaseCallbackHandler]", handler_class)()
            )
            if handler_class is None:
                if not any(
                    handler is var_handler  # direct pointer comparison
                    for handler in callback_manager.handlers
                ):
                    callback_manager.add_handler(var_handler, inheritable)
            elif not any(
                isinstance(handler, handler_class)
                for handler in callback_manager.handlers
            ):
                callback_manager.add_handler(var_handler, inheritable)

    if tracing_metadata:
        langsmith_inheritable_metadata = {
            **tracing_metadata,
            **(langsmith_inheritable_metadata or {}),
        }

    if langsmith_inheritable_metadata or langsmith_inheritable_tags:
        callback_manager.handlers = [
            handler.copy_with_metadata_defaults(
                metadata=langsmith_inheritable_metadata,
                tags=langsmith_inheritable_tags,
            )
            if isinstance(handler, LangChainTracer)
            else handler
            for handler in callback_manager.handlers
        ]
        callback_manager.inheritable_handlers = [
            handler.copy_with_metadata_defaults(
                metadata=langsmith_inheritable_metadata,
                tags=langsmith_inheritable_tags,
            )
            if isinstance(handler, LangChainTracer)
            else handler
            for handler in callback_manager.inheritable_handlers
        ]
    return callback_manager