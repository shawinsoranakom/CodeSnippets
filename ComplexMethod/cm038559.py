def encode(
        self,
        prompts: PromptType | Sequence[PromptType] | DataPrompt,
        pooling_params: PoolingParams | Sequence[PoolingParams] | None = None,
        *,
        use_tqdm: bool | Callable[..., tqdm] = True,
        lora_request: list[LoRARequest] | LoRARequest | None = None,
        pooling_task: PoolingTask | None = None,
        tokenization_kwargs: dict[str, Any] | None = None,
    ) -> list[PoolingRequestOutput]:
        """Apply pooling to the hidden states corresponding to the input
        prompts.

        This class automatically batches the given prompts, considering
        the memory constraint. For the best performance, put all of your prompts
        into a single list and pass it to this method.

        Args:
            prompts: The prompts to the LLM. You may pass a sequence of prompts
                for batch inference. See [PromptType][vllm.inputs.PromptType]
                for more details about the format of each prompt.
            pooling_params: The pooling parameters for pooling. If None, we
                use the default pooling parameters.
            use_tqdm: If `True`, shows a tqdm progress bar.
                If a callable (e.g., `functools.partial(tqdm, leave=False)`),
                it is used to create the progress bar.
                If `False`, no progress bar is created.
            lora_request: LoRA request to use for generation, if any.
            pooling_task: Override the pooling task to use.
            tokenization_kwargs: Overrides for `tokenizer.encode`.

        Returns:
            A list of `PoolingRequestOutput` objects containing the
            pooled hidden states in the same order as the input prompts.
        """

        if isinstance(prompts, dict) and "data" in prompts and pooling_task != "plugin":
            raise ValueError(
                "The 'data' field is only supported for the 'plugin' pooling task."
            )
        self._verify_pooling_task(pooling_task)
        assert pooling_task is not None and pooling_task in self.pooling_io_processors

        io_processor = self.pooling_io_processors[pooling_task]

        if pooling_params is None:
            pooling_params = PoolingParams()

        ctx = OfflineInputsContext(
            prompts=prompts,
            pooling_params=pooling_params,
            tokenization_kwargs=tokenization_kwargs,
        )

        engine_inputs = io_processor.pre_process_offline(ctx)
        n_inputs = len(engine_inputs)
        assert ctx.pooling_params is not None

        params_seq = self._params_to_seq(ctx.pooling_params, n_inputs)

        for param in params_seq:
            if param.task is None:
                param.task = pooling_task
            elif pooling_task == "plugin":
                # `plugin` task uses io_processor.parse_request to verify inputs.
                # We actually allow plugin to overwrite pooling_task.
                pass
            elif param.task != pooling_task:
                msg = f"You cannot overwrite {param.task=!r} with {pooling_task=!r}!"
                raise ValueError(msg)

        seq_lora_requests = self._lora_request_to_seq(lora_request, n_inputs)
        seq_priority = self._priority_to_seq(None, n_inputs)

        self._render_and_add_requests(
            prompts=engine_inputs,
            params=params_seq,
            lora_requests=seq_lora_requests,
            priorities=seq_priority,
        )

        outputs = self._run_engine(use_tqdm=use_tqdm, output_type=PoolingRequestOutput)
        outputs = io_processor.post_process_offline(
            ctx=OfflineOutputsContext(outputs=outputs)
        )
        return outputs