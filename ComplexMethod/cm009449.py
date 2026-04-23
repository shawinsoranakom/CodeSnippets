def stream(
        self,
        input: LanguageModelInput,
        config: RunnableConfig | None = None,
        *,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        if type(self)._stream == BaseLLM._stream:  # noqa: SLF001
            # model doesn't implement streaming, so use default implementation
            yield self.invoke(input, config=config, stop=stop, **kwargs)
        else:
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
            callback_manager = CallbackManager.configure(
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
            (run_manager,) = callback_manager.on_llm_start(
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
                for chunk in self._stream(
                    prompt, stop=stop, run_manager=run_manager, **kwargs
                ):
                    yield chunk.text
                    if generation is None:
                        generation = chunk
                    else:
                        generation += chunk
            except BaseException as e:
                run_manager.on_llm_error(
                    e,
                    response=LLMResult(
                        generations=[[generation]] if generation else []
                    ),
                )
                raise

            if generation is None:
                err = ValueError("No generation chunks were returned")
                run_manager.on_llm_error(err, response=LLMResult(generations=[]))
                raise err

            run_manager.on_llm_end(LLMResult(generations=[[generation]]))