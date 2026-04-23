def _tool_factory(dec_func: Callable | Runnable) -> BaseTool:
            tool_description = description
            if isinstance(dec_func, Runnable):
                runnable = dec_func

                if runnable.input_schema.model_json_schema().get("type") != "object":
                    msg = "Runnable must have an object schema."
                    raise ValueError(msg)

                async def ainvoke_wrapper(
                    callbacks: Callbacks | None = None, **kwargs: Any
                ) -> Any:
                    return await runnable.ainvoke(kwargs, {"callbacks": callbacks})

                def invoke_wrapper(
                    callbacks: Callbacks | None = None, **kwargs: Any
                ) -> Any:
                    return runnable.invoke(kwargs, {"callbacks": callbacks})

                coroutine = ainvoke_wrapper
                func = invoke_wrapper
                schema: ArgsSchema | None = runnable.input_schema
                tool_description = description or repr(runnable)
            elif inspect.iscoroutinefunction(dec_func):
                coroutine = dec_func
                func = None
                schema = args_schema
            else:
                coroutine = None
                func = dec_func
                schema = args_schema

            if infer_schema or args_schema is not None:
                return StructuredTool.from_function(
                    func,
                    coroutine,
                    name=tool_name,
                    description=tool_description,
                    return_direct=return_direct,
                    args_schema=schema,
                    infer_schema=infer_schema,
                    response_format=response_format,
                    parse_docstring=parse_docstring,
                    error_on_invalid_docstring=error_on_invalid_docstring,
                    extras=extras,
                )
            # If someone doesn't want a schema applied, we must treat it as
            # a simple string->string function
            if dec_func.__doc__ is None:
                msg = (
                    "Function must have a docstring if "
                    "description not provided and infer_schema is False."
                )
                raise ValueError(msg)
            return Tool(
                name=tool_name,
                func=func,
                description=f"{tool_name} tool",
                return_direct=return_direct,
                coroutine=coroutine,
                response_format=response_format,
                extras=extras,
            )