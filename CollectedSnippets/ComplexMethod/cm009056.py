async def abatch_as_completed(
        self,
        inputs: Sequence[LanguageModelInput],
        config: RunnableConfig | Sequence[RunnableConfig] | None = None,
        *,
        return_exceptions: bool = False,
        **kwargs: Any,
    ) -> AsyncIterator[tuple[int, Any]]:
        config = config or None
        # If <= 1 config use the underlying models batch implementation.
        if config is None or isinstance(config, dict) or len(config) <= 1:
            if isinstance(config, list):
                config = config[0]
            async for x in self._model(
                cast("RunnableConfig", config),
            ).abatch_as_completed(  # type: ignore[call-overload]
                inputs,
                config=config,
                return_exceptions=return_exceptions,
                **kwargs,
            ):
                yield x
        # If multiple configs default to Runnable.batch which uses executor to invoke
        # in parallel.
        else:
            async for x in super().abatch_as_completed(  # type: ignore[call-overload]
                inputs,
                config=config,
                return_exceptions=return_exceptions,
                **kwargs,
            ):
                yield x