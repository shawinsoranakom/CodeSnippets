def _validate_v2_model_runner(self) -> None:
        """Check for features not yet supported by the V2 model runner."""
        unsupported: list[str] = []

        if self.model_config is not None and self.model_config.has_inner_state:
            unsupported.append("hybrid/mamba models")

        if self.parallel_config.prefill_context_parallel_size > 1:
            unsupported.append("prefill context parallelism")

        if (
            self.speculative_config is not None
            and self.speculative_config.method not in ("eagle", "eagle3", "mtp")
        ):
            unsupported.append(f"speculative method '{self.speculative_config.method}'")

        if self.parallel_config.enable_dbo:
            unsupported.append("dual batch overlap")

        if (
            self.model_config is not None
            and self.model_config.enable_return_routed_experts
        ):
            # Will be added by https://github.com/vllm-project/vllm/pull/38163
            unsupported.append("routed experts capture")

        if self.model_config is not None and self.model_config.logits_processors:
            unsupported.append("custom logits processors")

        if self.cache_config.kv_sharing_fast_prefill:
            # Will be added by https://github.com/vllm-project/vllm/pull/35045
            unsupported.append("KV sharing fast prefill")

        if self.ec_transfer_config is not None:
            # Will be added by https://github.com/vllm-project/vllm/pull/38390
            unsupported.append("EC transfer")

        if unsupported:
            raise ValueError(
                "VLLM_USE_V2_MODEL_RUNNER does not yet support: "
                + ", ".join(unsupported)
            )