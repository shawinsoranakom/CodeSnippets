def maybe_register_speculator(
        self,
        speculator: Any | None,
        speculative_config: Any | None,
        load_dummy_weights: bool,
    ) -> bool:
        # if speculator is a moe model, add it to eplb
        if (
            speculator is None
            or not hasattr(speculator, "model")
            or not self.parallel_config.enable_eplb
            or load_dummy_weights
        ):
            return False

        draft_model = speculator.model
        if not is_mixture_of_experts(draft_model):
            return False

        assert not self.parallel_config.enable_elastic_ep, (
            "Elastic EP is not supported with draft model."
        )
        assert speculative_config is not None
        assert speculative_config.draft_model_config is not None
        assert self.state is not None
        self.state.add_model(
            draft_model,
            speculative_config.draft_model_config,
        )
        self._has_registered_models = True
        return True