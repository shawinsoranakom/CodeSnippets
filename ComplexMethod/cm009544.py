async def _ainvoke(
        self,
        value: Input,
        run_manager: AsyncCallbackManagerForChainRun,
        config: RunnableConfig,
        **kwargs: Any,
    ) -> Output:
        if hasattr(self, "afunc"):
            afunc = self.afunc
        else:
            if inspect.isgeneratorfunction(self.func):

                def func(
                    value: Input,
                    run_manager: AsyncCallbackManagerForChainRun,
                    config: RunnableConfig,
                    **kwargs: Any,
                ) -> Output:
                    output: Output | None = None
                    for chunk in call_func_with_variable_args(
                        cast("Callable[[Input], Iterator[Output]]", self.func),
                        value,
                        config,
                        run_manager.get_sync(),
                        **kwargs,
                    ):
                        if output is None:
                            output = chunk
                        else:
                            try:
                                output = output + chunk  # type: ignore[operator]
                            except TypeError:
                                output = chunk
                    return cast("Output", output)

            else:

                def func(
                    value: Input,
                    run_manager: AsyncCallbackManagerForChainRun,
                    config: RunnableConfig,
                    **kwargs: Any,
                ) -> Output:
                    return call_func_with_variable_args(
                        self.func, value, config, run_manager.get_sync(), **kwargs
                    )

            @wraps(func)
            async def f(*args: Any, **kwargs: Any) -> Any:
                return await run_in_executor(config, func, *args, **kwargs)

            afunc = f

        if is_async_generator(afunc):
            output: Output | None = None
            async with aclosing(
                cast(
                    "AsyncGenerator[Any, Any]",
                    acall_func_with_variable_args(
                        cast("Callable", afunc),
                        value,
                        config,
                        run_manager,
                        **kwargs,
                    ),
                )
            ) as stream:
                async for chunk in cast(
                    "AsyncIterator[Output]",
                    stream,
                ):
                    if output is None:
                        output = chunk
                    else:
                        try:
                            output = output + chunk  # type: ignore[operator]
                        except TypeError:
                            output = chunk
        else:
            output = await acall_func_with_variable_args(
                cast("Callable", afunc), value, config, run_manager, **kwargs
            )
        # If the output is a Runnable, invoke it
        if isinstance(output, Runnable):
            recursion_limit = config["recursion_limit"]
            if recursion_limit <= 0:
                msg = (
                    f"Recursion limit reached when invoking {self} with input {value}."
                )
                raise RecursionError(msg)
            output = await output.ainvoke(
                value,
                patch_config(
                    config,
                    callbacks=run_manager.get_child(),
                    recursion_limit=recursion_limit - 1,
                ),
            )
        return cast("Output", output)