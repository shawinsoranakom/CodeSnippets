def _set_default_max_num_seqs_and_batched_tokens_args(
        self,
        usage_context: UsageContext | None,
        model_config: ModelConfig,
        parallel_config: ParallelConfig,
    ):
        world_size = self.pipeline_parallel_size * self.tensor_parallel_size
        (
            default_max_num_batched_tokens,
            default_max_num_seqs,
        ) = self.get_batch_defaults(world_size)

        orig_max_num_batched_tokens = self.max_num_batched_tokens
        orig_max_num_seqs = self.max_num_seqs

        if self.max_num_batched_tokens is None:
            if parallel_config.use_batched_dp_moe:
                self.max_num_batched_tokens = (
                    SchedulerConfig.DEFAULT_MAX_NUM_BATCHED_TOKENS_FOR_BATCHED_DP
                )
            else:
                self.max_num_batched_tokens = default_max_num_batched_tokens.get(
                    usage_context,
                    SchedulerConfig.DEFAULT_MAX_NUM_BATCHED_TOKENS,
                )

        if self.max_num_seqs is None:
            self.max_num_seqs = default_max_num_seqs.get(
                usage_context,
                SchedulerConfig.DEFAULT_MAX_NUM_SEQS,
            )

        # If throughput mode is set, double max_num_batched_tokens and max_num_seqs.
        if self.performance_mode == "throughput":
            if orig_max_num_batched_tokens is None:
                self.max_num_batched_tokens *= 2
            if orig_max_num_seqs is None:
                self.max_num_seqs *= 2

        if orig_max_num_batched_tokens is None:
            assert model_config.max_model_len is not None, (
                "max_model_len must be set by this point"
            )
            if not self.enable_chunked_prefill:
                # If max_model_len is too short, use the default for higher throughput.
                self.max_num_batched_tokens = max(
                    model_config.max_model_len,
                    self.max_num_batched_tokens,
                )

            # When using default settings,
            # Ensure max_num_batched_tokens does not exceed model limit.
            # Some models (e.g., Whisper) have embeddings tied to max length.
            self.max_num_batched_tokens = min(
                self.max_num_seqs * model_config.max_model_len,
                self.max_num_batched_tokens,
            )

            logger.debug(
                "Defaulting max_num_batched_tokens to %d for %s usage context.",
                self.max_num_batched_tokens,
                usage_context.value if usage_context else None,
            )

        if orig_max_num_seqs is None:
            assert self.max_num_batched_tokens is not None  # For type checking
            self.max_num_seqs = min(self.max_num_seqs, self.max_num_batched_tokens)

            logger.debug(
                "Defaulting max_num_seqs to %d for %s usage context.",
                self.max_num_seqs,
                usage_context.value if usage_context else None,
            )