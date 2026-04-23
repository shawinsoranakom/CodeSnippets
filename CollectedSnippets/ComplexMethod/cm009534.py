async def _abatch_with_config(
        self,
        func: Callable[[list[Input]], Awaitable[list[Exception | Output]]]
        | Callable[
            [list[Input], list[AsyncCallbackManagerForChainRun]],
            Awaitable[list[Exception | Output]],
        ]
        | Callable[
            [list[Input], list[AsyncCallbackManagerForChainRun], list[RunnableConfig]],
            Awaitable[list[Exception | Output]],
        ],
        inputs: list[Input],
        config: RunnableConfig | list[RunnableConfig] | None = None,
        *,
        return_exceptions: bool = False,
        run_type: str | None = None,
        **kwargs: Any | None,
    ) -> list[Output]:
        """Transform a list of inputs to a list of outputs, with callbacks.

        Helper method to transform an `Input` value to an `Output` value,
        with callbacks.

        Use this method to implement `invoke` in subclasses.

        """
        if not inputs:
            return []

        configs = get_config_list(config, len(inputs))
        callback_managers = [get_async_callback_manager_for_config(c) for c in configs]
        run_managers: list[AsyncCallbackManagerForChainRun] = await asyncio.gather(
            *(
                callback_manager.on_chain_start(
                    None,
                    input_,
                    run_type=run_type,
                    name=config.get("run_name") or self.get_name(),
                    run_id=config.pop("run_id", None),
                )
                for callback_manager, input_, config in zip(
                    callback_managers, inputs, configs, strict=False
                )
            )
        )
        try:
            if accepts_config(func):
                kwargs["config"] = [
                    patch_config(c, callbacks=rm.get_child())
                    for c, rm in zip(configs, run_managers, strict=False)
                ]
            if accepts_run_manager(func):
                kwargs["run_manager"] = run_managers
            output = await func(inputs, **kwargs)  # type: ignore[call-arg]
        except BaseException as e:
            await asyncio.gather(
                *(run_manager.on_chain_error(e) for run_manager in run_managers)
            )
            if return_exceptions:
                return cast("list[Output]", [e for _ in inputs])
            raise
        else:
            first_exception: Exception | None = None
            coros: list[Awaitable[None]] = []
            for run_manager, out in zip(run_managers, output, strict=False):
                if isinstance(out, Exception):
                    first_exception = first_exception or out
                    coros.append(run_manager.on_chain_error(out))
                else:
                    coros.append(run_manager.on_chain_end(out))
            await asyncio.gather(*coros)
            if return_exceptions or first_exception is None:
                return cast("list[Output]", output)
            raise first_exception