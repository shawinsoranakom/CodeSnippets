def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.check_model_type(MODEL_FOR_CAUSAL_LM_MAPPING_NAMES)
        # Decoder-only models require left-padding for correct batched generation.
        # Only override when there is no feature_extractor, to avoid padding_side conflicts
        # (e.g., WhisperForCausalLM has a feature_extractor that pads on the right).
        if self.tokenizer is not None and self.tokenizer.padding_side == "right":
            self.tokenizer.padding_side = "left"

        if "prefix" not in self._preprocess_params:
            # This is very specific. The logic is quite complex and needs to be done
            # as a "default".
            # It also defines both some preprocess_kwargs and generate_kwargs
            # which is why we cannot put them in their respective methods.
            prefix = None
            if self.prefix is not None:
                prefix = self.prefix
            if prefix is None and self.model.__class__.__name__ in [
                "XLNetLMHeadModel",
                "TransfoXLLMHeadModel",
            ]:
                # For XLNet and TransformerXL we add an article to the prompt to give more state to the model.
                prefix = self.XL_PREFIX
            if prefix is not None:
                # Recalculate some generate_kwargs linked to prefix.
                preprocess_params, forward_params, _ = self._sanitize_parameters(prefix=prefix, **self._forward_params)
                self._preprocess_params = {**self._preprocess_params, **preprocess_params}
                self._forward_params = {**self._forward_params, **forward_params}