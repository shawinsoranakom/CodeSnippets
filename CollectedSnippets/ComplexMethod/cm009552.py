async def astream(
        self,
        input: Input,
        config: RunnableConfig | None = None,
        **kwargs: Any | None,
    ) -> AsyncIterator[Output]:
        if self.exception_key is not None and not isinstance(input, dict):
            msg = (
                "If 'exception_key' is specified then input must be a dictionary."
                f"However found a type of {type(input)} for input"
            )
            raise ValueError(msg)
        # setup callbacks
        config = ensure_config(config)
        callback_manager = get_async_callback_manager_for_config(config)
        # start the root run
        run_manager = await callback_manager.on_chain_start(
            None,
            input,
            name=config.get("run_name") or self.get_name(),
            run_id=config.pop("run_id", None),
        )
        first_error = None
        last_error = None
        for runnable in self.runnables:
            try:
                if self.exception_key and last_error is not None:
                    input[self.exception_key] = last_error  # type: ignore[index]
                child_config = patch_config(config, callbacks=run_manager.get_child())
                with set_config_context(child_config) as context:
                    stream = runnable.astream(
                        input,
                        child_config,
                        **kwargs,
                    )
                    chunk = await coro_with_context(anext(stream), context)
            except self.exceptions_to_handle as e:
                first_error = e if first_error is None else first_error
                last_error = e
            except BaseException as e:
                await run_manager.on_chain_error(e)
                raise
            else:
                first_error = None
                break
        if first_error:
            await run_manager.on_chain_error(first_error)
            raise first_error

        yield chunk
        output: Output | None = chunk
        try:
            async for chunk in stream:
                yield chunk
                try:
                    output = output + chunk  # type: ignore[operator]
                except TypeError:
                    output = None
        except BaseException as e:
            await run_manager.on_chain_error(e)
            raise
        await run_manager.on_chain_end(output)