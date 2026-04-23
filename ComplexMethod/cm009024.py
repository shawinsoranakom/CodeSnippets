def decorator(
        func: _CallableReturningModelResponse[StateT, ContextT, ResponseT],
    ) -> AgentMiddleware[StateT, ContextT]:
        is_async = iscoroutinefunction(func)

        if is_async:

            async def async_wrapped(
                _self: AgentMiddleware[StateT, ContextT],
                request: ModelRequest[ContextT],
                handler: Callable[[ModelRequest[ContextT]], Awaitable[ModelResponse[ResponseT]]],
            ) -> ModelResponse[ResponseT] | AIMessage:
                return await func(request, handler)  # type: ignore[misc, arg-type]

            middleware_name = name or cast(
                "str", getattr(func, "__name__", "WrapModelCallMiddleware")
            )

            return type(
                middleware_name,
                (AgentMiddleware,),
                {
                    "state_schema": state_schema or AgentState,
                    "tools": tools or [],
                    "awrap_model_call": async_wrapped,
                },
            )()

        def wrapped(
            _self: AgentMiddleware[StateT, ContextT],
            request: ModelRequest[ContextT],
            handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
        ) -> ModelResponse[ResponseT] | AIMessage:
            return func(request, handler)

        middleware_name = name or cast("str", getattr(func, "__name__", "WrapModelCallMiddleware"))

        return type(
            middleware_name,
            (AgentMiddleware,),
            {
                "state_schema": state_schema or AgentState,
                "tools": tools or [],
                "wrap_model_call": wrapped,
            },
        )()