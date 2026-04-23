def _validate_params(
        self,
        params: SamplingParams | PoolingParams,
        supported_tasks: tuple[SupportedTask, ...],
    ) -> None:
        """Raise `ValueError` if SamplingParams or PoolingParams is not valid."""
        if isinstance(params, SamplingParams):
            supported_generation_tasks = [
                task for task in supported_tasks if task in GENERATION_TASKS
            ]
            if not supported_generation_tasks:
                raise ValueError("This model does not support generation")

            params.verify(
                self.model_config,
                self.speculative_config,
                self.structured_outputs_config,
                self.tokenizer,
            )

            if params.thinking_token_budget is not None and (
                self.vllm_config.reasoning_config is None
                or not self.vllm_config.reasoning_config.enabled
            ):
                raise ValueError(
                    "thinking_token_budget is set but reasoning_config is "
                    "not configured. Please set --reasoning-config to use "
                    "thinking_token_budget."
                )
        elif isinstance(params, PoolingParams):
            supported_pooling_tasks = [
                task for task in supported_tasks if task in POOLING_TASKS
            ]
            if not supported_pooling_tasks:
                raise ValueError("This model does not support pooling")

            if params.task is None:
                if "token_embed" in supported_pooling_tasks:
                    params.task = "token_embed"
                elif "token_classify" in supported_pooling_tasks:
                    params.task = "token_classify"
                elif "plugin" in supported_pooling_tasks:
                    params.task = "plugin"

            if params.task not in supported_pooling_tasks:
                raise ValueError(
                    f"Unsupported task: {params.task!r} "
                    f"Supported tasks: {supported_pooling_tasks}"
                )

            params.verify(self.model_config)
        else:
            raise TypeError(
                f"params must be either SamplingParams or PoolingParams, "
                f"but got {type(params).__name__}"
            )