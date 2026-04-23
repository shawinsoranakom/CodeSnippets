async def _atransform(
        self,
        chunks: AsyncIterator[Input],
        run_manager: AsyncCallbackManagerForChainRun,
        config: RunnableConfig,
        **kwargs: Any,
    ) -> AsyncIterator[Output]:
        final: Input
        got_first_val = False
        async for ichunk in chunks:
            # By definitions, RunnableLambdas consume all input before emitting output.
            # If the input is not addable, then we'll assume that we can
            # only operate on the last chunk.
            # So we'll iterate until we get to the last chunk!
            if not got_first_val:
                final = ichunk
                got_first_val = True
            else:
                try:
                    final = final + ichunk  # type: ignore[operator]
                except TypeError:
                    final = ichunk

        if hasattr(self, "afunc"):
            afunc = self.afunc
        else:
            if inspect.isgeneratorfunction(self.func):
                msg = (
                    "Cannot stream from a generator function asynchronously."
                    "Use .stream() instead."
                )
                raise TypeError(msg)

            def func(
                input_: Input,
                run_manager: AsyncCallbackManagerForChainRun,
                config: RunnableConfig,
                **kwargs: Any,
            ) -> Output:
                return call_func_with_variable_args(
                    self.func, input_, config, run_manager.get_sync(), **kwargs
                )

            @wraps(func)
            async def f(*args: Any, **kwargs: Any) -> Any:
                return await run_in_executor(config, func, *args, **kwargs)

            afunc = f

        if is_async_generator(afunc):
            output: Output | None = None
            async for chunk in cast(
                "AsyncIterator[Output]",
                acall_func_with_variable_args(
                    cast("Callable", afunc),
                    final,
                    config,
                    run_manager,
                    **kwargs,
                ),
            ):
                yield chunk
                if output is None:
                    output = chunk
                else:
                    try:
                        output = output + chunk  # type: ignore[operator]
                    except TypeError:
                        output = chunk
        else:
            output = await acall_func_with_variable_args(
                cast("Callable", afunc),
                final,
                config,
                run_manager,
                **kwargs,
            )

        # If the output is a Runnable, use its astream output
        if isinstance(output, Runnable):
            recursion_limit = config["recursion_limit"]
            if recursion_limit <= 0:
                msg = (
                    f"Recursion limit reached when invoking {self} with input {final}."
                )
                raise RecursionError(msg)
            async for chunk in output.astream(
                final,
                patch_config(
                    config,
                    callbacks=run_manager.get_child(),
                    recursion_limit=recursion_limit - 1,
                ),
            ):
                yield chunk
        elif not is_async_generator(afunc):
            # Otherwise, just yield it
            yield cast("Output", output)