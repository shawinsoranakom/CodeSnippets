def _initialize_missing_keys(self, is_quantized: bool) -> None:
        """
        Initialize the missing keys (keys that are part of the model parameters, but were NOT found in the loaded state dicts), according to
        `_initialize_weights`. Indeed, since the corresponding weights are missing from the state dict, they will not be replaced and need to
        be initialized correctly (i.e. weight initialization distribution).

        Also marks non-missing params/buffers with `_is_hf_initialized` and propagates this flag to modules,
        so that `_initialize_weights` can skip fully-initialized modules entirely.
        """
        if is_fsdp_enabled() and not is_local_dist_rank_0():
            # Handle FSDP edge case when using cpu ram efficient loading to ensure it is marked as initialized
            # since it will get its weights broadcasted from rank0
            # We actually need to do that only because we want to re-initialize non-persistent buffers with correct values.
            # Everything else in the state_dict will be gathered from rank0, so we don't need re-initialization.
            # We could simply early return after buffer inits if we had a way to init only the non-persistent buffers
            for key in self.state_dict():
                try:
                    param_or_buffer = self.get_parameter_or_buffer(key)
                    param_or_buffer._is_hf_initialized = True
                except AttributeError:
                    pass  # may happen when handling pre-quantized weights
            self._is_hf_initialized = True

        # This will only initialize submodules that are not marked as initialized by the line above.
        if is_deepspeed_zero3_enabled() and not is_quantized:
            import deepspeed

            # keep_vars=True as we need the original tensors, so that the "_is_hf_initialized" is present on them
            not_initialized_parameters = list(
                {v for v in self.state_dict(keep_vars=True).values() if not getattr(v, "_is_hf_initialized", False)}
            )
            with deepspeed.zero.GatheredParameters(not_initialized_parameters, modifier_rank=0):
                self.initialize_weights()
        else:
            self.initialize_weights()