def score(
        self,
        data_1: ScoreInput | list[ScoreInput],
        data_2: ScoreInput | list[ScoreInput],
        /,
        *,
        use_tqdm: bool | Callable[..., tqdm] = True,
        pooling_params: PoolingParams | None = None,
        lora_request: list[LoRARequest] | LoRARequest | None = None,
        tokenization_kwargs: dict[str, Any] | None = None,
        chat_template: str | None = None,
    ) -> list[ScoringRequestOutput]:
        """Generate similarity scores for all pairs `<text,text_pair>` or
          `<multi-modal data, multi-modal data pair>`.

        The inputs can be `1 -> 1`, `1 -> N` or `N -> N`.
        In the `1 - N` case the `data_1` input will be replicated `N`
        times to pair with the `data_2` inputs.
        The input pairs are used to build a list of prompts for the
        cross encoder model. This class automatically batches the prompts,
        considering the memory constraint. For the best performance, put all
        of your inputs into a single list and pass it to this method.

        Supports both text and multi-modal data (images, etc.) when used with
        appropriate multi-modal models. For multi-modal inputs, ensure the
        prompt structure matches the model's expected input format.

        Args:
            data_1: Can be a single prompt, a list of prompts or
                `ScoreMultiModalParam`, which can contain either text or
                multi-modal data. When a list, it must have the same length as
                the `data_2` list.
            data_2: The data to pair with the query to form the input to
                the LLM. Can be text or multi-modal data. See [PromptType]
                [vllm.inputs.PromptType] for more details about the format of
                each prompt.
            pooling_params: The pooling parameters for pooling. If None, we
                use the default pooling parameters.
            use_tqdm: If `True`, shows a tqdm progress bar.
                If a callable (e.g., `functools.partial(tqdm, leave=False)`),
                it is used to create the progress bar.
                If `False`, no progress bar is created.
            lora_request: LoRA request to use for generation, if any.
            chat_template: The chat template to use for the scoring. If None, we
                use the model's default chat template.
            tokenization_kwargs: Overrides for `tokenizer.encode`.
        Returns:
            A list of `ScoringRequestOutput` objects containing the
            generated scores in the same order as the input prompts.
        """

        if self.runner_type != "pooling":
            raise ValueError(
                "LLM.score() is only supported for pooling models. "
                "Try passing `--runner pooling` to use the model as a "
                "pooling model."
            )

        score_type: str | None = SCORE_TYPE_MAP.get(self.pooling_task, None)  # type: ignore[arg-type]
        if (
            score_type == "cross-encoder"
            and getattr(self.model_config.hf_config, "num_labels", 0) != 1
        ):
            raise ValueError("Scoring API is only enabled for num_labels == 1.")

        if score_type is None or score_type not in self.pooling_io_processors:
            raise ValueError("This model does not support the Scoring API.")

        io_processor = self.pooling_io_processors[score_type]
        assert isinstance(io_processor, ScoringIOProcessor)

        pooling_task = io_processor.pooling_task
        scoring_data = io_processor.valid_inputs(data_1, data_2)
        n_queries = len(scoring_data.data_1)

        if pooling_params is None:
            pooling_params = PoolingParams()

        ctx = OfflineInputsContext(
            prompts=scoring_data,
            pooling_params=pooling_params,
            tokenization_kwargs=tokenization_kwargs,
            chat_template=chat_template,
            n_queries=n_queries,
        )

        engine_inputs = io_processor.pre_process_offline(ctx)
        n_inputs = len(engine_inputs)

        seq_lora_requests = self._lora_request_to_seq(lora_request, n_inputs)
        params_seq = self._params_to_seq(ctx.pooling_params, n_inputs)

        for param in params_seq:
            if param.task is None:
                param.task = pooling_task
            elif param.task != pooling_task:
                msg = f"You cannot overwrite {param.task=!r} with {pooling_task=!r}!"
                raise ValueError(msg)

        seq_priority = self._priority_to_seq(None, n_inputs)

        self._render_and_add_requests(
            prompts=engine_inputs,
            params=params_seq,
            lora_requests=seq_lora_requests,
            priorities=seq_priority,
        )

        outputs = self._run_engine(use_tqdm=use_tqdm, output_type=PoolingRequestOutput)
        outputs = io_processor.post_process_offline(
            ctx=OfflineOutputsContext(outputs=outputs, n_queries=n_queries),
        )

        return [ScoringRequestOutput.from_base(item) for item in outputs]