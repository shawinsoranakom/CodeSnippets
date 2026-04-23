def generate(
        self,
        prompts: list[str],
        stop: list[str] | None = None,
        callbacks: Callbacks | list[Callbacks] | None = None,
        *,
        tags: list[str] | list[list[str]] | None = None,
        metadata: dict[str, Any] | list[dict[str, Any]] | None = None,
        run_name: str | list[str] | None = None,
        run_id: uuid.UUID | list[uuid.UUID | None] | None = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Pass a sequence of prompts to a model and return generations.

        This method should make use of batched calls for models that expose a batched
        API.

        Use this method when you want to:

        1. Take advantage of batched calls,
        2. Need more output from the model than just the top generated value,
        3. Are building chains that are agnostic to the underlying language model
            type (e.g., pure text completion models vs chat models).

        Args:
            prompts: List of string prompts.
            stop: Stop words to use when generating.

                Model output is cut off at the first occurrence of any of these
                substrings.
            callbacks: `Callbacks` to pass through.

                Used for executing additional functionality, such as logging or
                streaming, throughout generation.
            tags: List of tags to associate with each prompt. If provided, the length
                of the list must match the length of the prompts list.
            metadata: List of metadata dictionaries to associate with each prompt. If
                provided, the length of the list must match the length of the prompts
                list.
            run_name: List of run names to associate with each prompt. If provided, the
                length of the list must match the length of the prompts list.
            run_id: List of run IDs to associate with each prompt. If provided, the
                length of the list must match the length of the prompts list.
            **kwargs: Arbitrary additional keyword arguments.

                These are usually passed to the model provider API call.

        Raises:
            ValueError: If prompts is not a list.
            ValueError: If the length of `callbacks`, `tags`, `metadata`, or
                `run_name` (if provided) does not match the length of prompts.

        Returns:
            An `LLMResult`, which contains a list of candidate `Generations` for each
                input prompt and additional model provider-specific output.
        """
        if not isinstance(prompts, list):
            msg = (
                "Argument 'prompts' is expected to be of type list[str], received"
                f" argument of type {type(prompts)}."
            )
            raise ValueError(msg)  # noqa: TRY004
        # Create callback managers
        if isinstance(metadata, list):
            metadata = [
                {
                    **(meta or {}),
                    **self._get_ls_params_with_defaults(stop=stop, **kwargs),
                }
                for meta in metadata
            ]
        elif isinstance(metadata, dict):
            metadata = {
                **(metadata or {}),
                **self._get_ls_params_with_defaults(stop=stop, **kwargs),
            }
        if (
            isinstance(callbacks, list)
            and callbacks
            and (
                isinstance(callbacks[0], (list, BaseCallbackManager))
                or callbacks[0] is None
            )
        ):
            # We've received a list of callbacks args to apply to each input
            if len(callbacks) != len(prompts):
                msg = "callbacks must be the same length as prompts"
                raise ValueError(msg)
            if tags is not None and not (
                isinstance(tags, list) and len(tags) == len(prompts)
            ):
                msg = "tags must be a list of the same length as prompts"
                raise ValueError(msg)
            if metadata is not None and not (
                isinstance(metadata, list) and len(metadata) == len(prompts)
            ):
                msg = "metadata must be a list of the same length as prompts"
                raise ValueError(msg)
            if run_name is not None and not (
                isinstance(run_name, list) and len(run_name) == len(prompts)
            ):
                msg = "run_name must be a list of the same length as prompts"
                raise ValueError(msg)
            callbacks = cast("list[Callbacks]", callbacks)
            tags_list = cast("list[list[str] | None]", tags or ([None] * len(prompts)))
            metadata_list = cast(
                "list[dict[str, Any] | None]", metadata or ([{}] * len(prompts))
            )
            run_name_list = run_name or cast(
                "list[str | None]", ([None] * len(prompts))
            )
            params = self.dict()
            params["stop"] = stop
            callback_managers = [
                CallbackManager.configure(
                    callback,
                    self.callbacks,
                    self.verbose,
                    tag,
                    self.tags,
                    meta,
                    self.metadata,
                    langsmith_inheritable_metadata=_filter_invocation_params_for_tracing(
                        params
                    ),
                )
                for callback, tag, meta in zip(
                    callbacks, tags_list, metadata_list, strict=False
                )
            ]
        else:
            # We've received a single callbacks arg to apply to all inputs
            params = self.dict()
            params["stop"] = stop
            callback_managers = [
                CallbackManager.configure(
                    cast("Callbacks", callbacks),
                    self.callbacks,
                    self.verbose,
                    cast("list[str]", tags),
                    self.tags,
                    cast("dict[str, Any]", metadata),
                    self.metadata,
                    langsmith_inheritable_metadata=_filter_invocation_params_for_tracing(
                        params
                    ),
                )
            ] * len(prompts)
            run_name_list = [cast("str | None", run_name)] * len(prompts)
        run_ids_list = self._get_run_ids_list(run_id, prompts)
        options = {"stop": stop}
        (
            existing_prompts,
            llm_string,
            missing_prompt_idxs,
            missing_prompts,
        ) = get_prompts(params, prompts, self.cache)
        new_arg_supported = inspect.signature(self._generate).parameters.get(
            "run_manager"
        )
        if (self.cache is None and get_llm_cache() is None) or self.cache is False:
            run_managers = [
                callback_manager.on_llm_start(
                    self._serialized,
                    [prompt],
                    invocation_params=params,
                    options=options,
                    name=run_name,
                    batch_size=len(prompts),
                    run_id=run_id_,
                )[0]
                for callback_manager, prompt, run_name, run_id_ in zip(
                    callback_managers,
                    prompts,
                    run_name_list,
                    run_ids_list,
                    strict=False,
                )
            ]
            return self._generate_helper(
                prompts,
                stop,
                run_managers,
                new_arg_supported=bool(new_arg_supported),
                **kwargs,
            )
        if len(missing_prompts) > 0:
            run_managers = [
                callback_managers[idx].on_llm_start(
                    self._serialized,
                    [prompts[idx]],
                    invocation_params=params,
                    options=options,
                    name=run_name_list[idx],
                    batch_size=len(missing_prompts),
                )[0]
                for idx in missing_prompt_idxs
            ]
            new_results = self._generate_helper(
                missing_prompts,
                stop,
                run_managers,
                new_arg_supported=bool(new_arg_supported),
                **kwargs,
            )
            llm_output = update_cache(
                self.cache,
                existing_prompts,
                llm_string,
                missing_prompt_idxs,
                new_results,
                prompts,
            )
            run_info = (
                [RunInfo(run_id=run_manager.run_id) for run_manager in run_managers]
                if run_managers
                else None
            )
        else:
            llm_output = {}
            run_info = None
        generations = [existing_prompts[i] for i in range(len(prompts))]
        return LLMResult(generations=generations, llm_output=llm_output, run=run_info)