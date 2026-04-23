def compute_hash(self) -> str:
        """
        WARNING: Whenever a new field is added to this config,
        ensure that it is included in the factors list if
        it affects the computation graph.

        Provide a hash that uniquely identifies all the configs
        that affect the structure of the computation
        graph from input ids/embeddings to the final hidden states,
        excluding anything before input ids/embeddings and after
        the final hidden states.
        """
        factors: list[Any] = []

        # summarize vllm config
        vllm_factors: list[Any] = []
        from vllm import __version__

        vllm_factors.append(__version__)
        if self.model_config:
            vllm_factors.append(self.model_config.compute_hash())
            if (
                self.compilation_config
                and getattr(self.compilation_config, "compile_mm_encoder", False)
                and self.model_config.multimodal_config
            ):
                vllm_factors.append(self.model_config.multimodal_config.compute_hash())
        else:
            vllm_factors.append("None")
        if self.cache_config:
            vllm_factors.append(self.cache_config.compute_hash())
        else:
            vllm_factors.append("None")
        if self.parallel_config:
            vllm_factors.append(self.parallel_config.compute_hash())
        else:
            vllm_factors.append("None")
        if self.scheduler_config:
            vllm_factors.append(self.scheduler_config.compute_hash())
        else:
            vllm_factors.append("None")
        if self.device_config:
            vllm_factors.append(self.device_config.compute_hash())
        else:
            vllm_factors.append("None")
        if self.load_config:
            vllm_factors.append(self.load_config.compute_hash())
        else:
            vllm_factors.append("None")
        if self.offload_config:
            vllm_factors.append(self.offload_config.compute_hash())
        else:
            vllm_factors.append("None")
        if self.attention_config:
            vllm_factors.append(self.attention_config.compute_hash())
        else:
            vllm_factors.append("None")
        if self.lora_config:
            vllm_factors.append(self.lora_config.compute_hash())
        else:
            vllm_factors.append("None")
        if self.speculative_config:
            vllm_factors.append(self.speculative_config.compute_hash())
        else:
            vllm_factors.append("None")
        if self.structured_outputs_config:
            vllm_factors.append(self.structured_outputs_config.compute_hash())
        if self.profiler_config:
            vllm_factors.append(self.profiler_config.compute_hash())
        else:
            vllm_factors.append("None")
        vllm_factors.append(self.observability_config.compute_hash())
        if self.quant_config:
            pass  # should be captured by model_config.quantization
        if self.compilation_config:
            vllm_factors.append(self.compilation_config.compute_hash())
        else:
            vllm_factors.append("None")
        if self.kernel_config:
            vllm_factors.append(self.kernel_config.compute_hash())
        else:
            vllm_factors.append(None)
        if self.kv_transfer_config:
            vllm_factors.append(self.kv_transfer_config.compute_hash())
        else:
            vllm_factors.append("None")
        if self.ec_transfer_config:
            vllm_factors.append(self.ec_transfer_config.compute_hash())
        else:
            vllm_factors.append("None")
        if self.additional_config:
            if isinstance(additional_config := self.additional_config, dict):
                additional_config_hash = safe_hash(
                    json.dumps(additional_config, sort_keys=True).encode(),
                    usedforsecurity=False,
                ).hexdigest()
            else:
                additional_config_hash = additional_config.compute_hash()
            vllm_factors.append(additional_config_hash)
        else:
            vllm_factors.append("None")
        factors.append(vllm_factors)

        hash_str = safe_hash(str(factors).encode(), usedforsecurity=False).hexdigest()[
            :10
        ]
        return hash_str