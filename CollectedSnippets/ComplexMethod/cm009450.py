async def astream(
        self,
        input: LanguageModelInput,
        config: RunnableConfig | None = None,
        *,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        if (
            type(self)._astream is BaseLLM._astream  # noqa: SLF001
            and type(self)._stream is BaseLLM._stream  # noqa: SLF001
        ):
            yield await self.ainvoke(input, config=config, stop=stop, **kwargs)
            return

        prompt = self._convert_input(input).to_string()
        config = ensure_config(config)
        params = self.dict()
        params["stop"] = stop
        params = {**params, **kwargs}
        options = {"stop": stop}
        inheritable_metadata = {
            **(config.get("metadata") or {}),
            **self._get_ls_params_with_defaults(stop=stop, **kwargs),
        }
        callback_manager = AsyncCallbackManager.configure(
            config.get("callbacks"),
            self.callbacks,
            self.verbose,
            config.get("tags"),
            self.tags,
            inheritable_metadata,
            self.metadata,
            langsmith_inheritable_metadata=_filter_invocation_params_for_tracing(
                params
            ),
        )
        (run_manager,) = await callback_manager.on_llm_start(
            self._serialized,
            [prompt],
            invocation_params=params,
            options=options,
            name=config.get("run_name"),
            run_id=config.pop("run_id", None),
            batch_size=1,
        )
        generation: GenerationChunk | None = None
        try:
            async for chunk in self._astream(
                prompt,
                stop=stop,
                run_manager=run_manager,
                **kwargs,
            ):
                yield chunk.text
                if generation is None:
                    generation = chunk
                else:
                    generation += chunk
        except BaseException as e:
            await run_manager.on_llm_error(
                e,
                response=LLMResult(generations=[[generation]] if generation else []),
            )
            raise

        if generation is None:
            err = ValueError("No generation chunks were returned")
            await run_manager.on_llm_error(err, response=LLMResult(generations=[]))
            raise err

        await run_manager.on_llm_end(LLMResult(generations=[[generation]]))