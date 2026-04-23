def _unsloth_pre_compute_loss(self, model, inputs, *args, **kwargs):
    num_items_in_batch = None

    if "num_items_in_batch" in kwargs:
        num_items_in_batch = kwargs["num_items_in_batch"]
        if num_items_in_batch is None:
            # Remove it since the model does not support it!
            kwargs.pop("num_items_in_batch")
        elif "num_items_in_batch" not in inputs:
            inputs["num_items_in_batch"] = num_items_in_batch

    # Get gradient accumulation steps if possible
    if (
        num_items_in_batch is None
        and getattr(getattr(self, "args", self), "gradient_accumulation_steps", 1) != 1
    ):
        inner_model = model
        if hasattr(inner_model, "base_model"):
            inner_model = inner_model.base_model
        if hasattr(inner_model, "model"):
            inner_model = inner_model.model
        name = inner_model.__class__.__name__

        logger.warning_once(
            f"Unsloth: Not an error, but {name} does not accept `num_items_in_batch`.\n"
            "Using gradient accumulation will be very slightly less accurate.\n"
            "Read more on gradient accumulation issues here: https://unsloth.ai/blog/gradient"
        )
    # Gemma3 multimodal models in transformers 5.x require token_type_ids during training.
    # For text-only SFT, token_type_ids should be all zeros (no image tokens).
    if "token_type_ids" not in inputs and "input_ids" in inputs:
        _inner = model
        for _attr in ("base_model", "model", "model"):
            _inner = getattr(_inner, _attr, _inner)
        if getattr(getattr(_inner, "config", None), "model_type", "") in ("gemma3",):
            import sys as _sys

            _mod = _sys.modules.get(type(_inner).__module__)
            _has_ccm = _mod is not None and hasattr(_mod, "create_causal_mask_mapping")
            if _has_ccm and _inner.training:
                inputs["token_type_ids"] = torch.zeros_like(inputs["input_ids"])
    # Gemma4 uses mm_token_type_ids (not token_type_ids) for VLM masking
    if "mm_token_type_ids" not in inputs and "input_ids" in inputs:
        _inner = model
        for _attr in ("base_model", "model", "model"):
            _inner = getattr(_inner, _attr, _inner)
        if getattr(getattr(_inner, "config", None), "model_type", "") in ("gemma4",):
            import sys as _sys

            _mod = _sys.modules.get(type(_inner).__module__)
            _has_ccm = _mod is not None and hasattr(_mod, "create_causal_mask_mapping")
            if _has_ccm and _inner.training:
                inputs["mm_token_type_ids"] = torch.zeros_like(inputs["input_ids"])

    outputs = self._old_compute_loss(model, inputs, *args, **kwargs)
    return outputs