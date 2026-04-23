def _get_transformers_backend_cls(self) -> str:
        """Determine which Transformers modeling backend class will be used if
        `model_impl` is set to `transformers` or `auto`."""
        cls = "Transformers"
        # If 'hf_config != hf_text_config' it's a nested config, i.e. multimodal
        cls += "MultiModal" if self.hf_config != self.hf_text_config else ""
        cls += "MoE" if self.is_moe else ""
        # Check if the architecture we're wrapping has defaults
        runner = None
        task = None
        if defaults := try_match_architecture_defaults(self.architectures[0]):
            _, (runner, task) = defaults
        # User specified value take precedence
        if self.runner != "auto":
            runner = self.runner
        # Only consider Transformers modeling backend pooling classes if we're wrapping
        # an architecture that defaults to pooling. Otherwise, we return the LM class
        # and use adapters.
        if runner == "pooling" and task in {"embed", "classify"}:
            if task == "embed":
                cls += "EmbeddingModel"
            elif task == "classify":
                cls += "ForSequenceClassification"
        else:
            cls += "ForCausalLM"
        return cls