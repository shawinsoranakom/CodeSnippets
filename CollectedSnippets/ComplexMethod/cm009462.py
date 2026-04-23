def generate(
        self,
        messages: list[list[BaseMessage]],
        stop: list[str] | None = None,
        callbacks: Callbacks = None,
        *,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        run_name: str | None = None,
        run_id: uuid.UUID | None = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Pass a sequence of prompts to the model and return model generations.

        This method should make use of batched calls for models that expose a batched
        API.

        Use this method when you want to:

        1. Take advantage of batched calls,
        2. Need more output from the model than just the top generated value,
        3. Are building chains that are agnostic to the underlying language model
            type (e.g., pure text completion models vs chat models).

        Args:
            messages: List of list of messages.
            stop: Stop words to use when generating.

                Model output is cut off at the first occurrence of any of these
                substrings.
            callbacks: `Callbacks` to pass through.

                Used for executing additional functionality, such as logging or
                streaming, throughout generation.
            tags: The tags to apply.
            metadata: The metadata to apply.
            run_name: The name of the run.
            run_id: The ID of the run.
            **kwargs: Arbitrary additional keyword arguments.

                These are usually passed to the model provider API call.

        Returns:
            An `LLMResult`, which contains a list of candidate `Generations` for each
                input prompt and additional model provider-specific output.

        """
        ls_structured_output_format = kwargs.pop(
            "ls_structured_output_format", None
        ) or kwargs.pop("structured_output_format", None)
        ls_structured_output_format_dict = _format_ls_structured_output(
            ls_structured_output_format
        )

        params = self._get_invocation_params(stop=stop, **kwargs)
        options = {"stop": stop, **ls_structured_output_format_dict}
        inheritable_metadata = {
            **(metadata or {}),
            **self._get_ls_params_with_defaults(stop=stop, **kwargs),
        }

        callback_manager = CallbackManager.configure(
            callbacks,
            self.callbacks,
            self.verbose,
            tags,
            self.tags,
            inheritable_metadata,
            self.metadata,
            langsmith_inheritable_metadata=_filter_invocation_params_for_tracing(
                params
            ),
        )
        messages_to_trace = [
            _format_for_tracing(message_list) for message_list in messages
        ]
        run_managers = callback_manager.on_chat_model_start(
            self._serialized,
            messages_to_trace,
            invocation_params=params,
            options=options,
            name=run_name,
            run_id=run_id,
            batch_size=len(messages),
        )
        results = []
        input_messages = [
            _normalize_messages(message_list) for message_list in messages
        ]
        for i, m in enumerate(input_messages):
            try:
                results.append(
                    self._generate_with_cache(
                        m,
                        stop=stop,
                        run_manager=run_managers[i] if run_managers else None,
                        **kwargs,
                    )
                )
            except BaseException as e:
                if run_managers:
                    generations_with_error_metadata = _generate_response_from_error(e)
                    run_managers[i].on_llm_error(
                        e,
                        response=LLMResult(
                            generations=[generations_with_error_metadata]
                        ),
                    )
                raise
        flattened_outputs = [
            LLMResult(generations=[res.generations], llm_output=res.llm_output)
            for res in results
        ]
        llm_output = self._combine_llm_outputs([res.llm_output for res in results])
        generations = [res.generations for res in results]
        output = LLMResult(generations=generations, llm_output=llm_output)
        if run_managers:
            run_infos = []
            for manager, flattened_output in zip(
                run_managers, flattened_outputs, strict=False
            ):
                manager.on_llm_end(flattened_output)
                run_infos.append(RunInfo(run_id=manager.run_id))
            output.run = run_infos
        return output