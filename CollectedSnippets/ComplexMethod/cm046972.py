def unsloth_fast_generate(
    self,
    *args,
    **kwargs,
):
    # If the model starts out in training mode, restore training mode after generation
    restore_training_mode = self.training

    FastLlamaModel.for_inference(self)

    # Unpack BatchEncoding passed as input_ids for backwards compatibility.
    # Old notebooks do model.generate(input_ids=tokenizer(...)) where the tokenizer
    # output is a BatchEncoding (dict-like). Transformers v5 generate() calls
    # .shape on it directly and crashes. Unpack into separate kwargs so both
    # v4 and v5 work transparently.
    _maybe_encoding = kwargs.get("input_ids", None)
    if (
        _maybe_encoding is not None
        and not isinstance(_maybe_encoding, torch.Tensor)
        and hasattr(_maybe_encoding, "items")
    ):
        batch_data = kwargs.pop("input_ids")
        for key, val in batch_data.items():
            kwargs.setdefault(key, val)

    dtype = _get_dtype(dtype_from_config(self.config))

    if hasattr(self, "config") and hasattr(self.config, "max_position_embeddings"):
        if (
            "input_ids" in kwargs
            and kwargs["input_ids"] is not None
            and "max_new_tokens" in kwargs
        ):
            _ids = kwargs["input_ids"]
            if hasattr(_ids, "shape") and (
                _ids.shape[-1] + kwargs["max_new_tokens"]
                > self.config.max_position_embeddings
            ):
                raise ValueError(
                    f"Unsloth: input length {_ids.shape[-1]} + max_new_tokens {kwargs['max_new_tokens']} exceeds the maximum sequence length of {self.config.max_position_embeddings}!\n"
                    "You will need to do long context extension by increasing the `max_seq_length` in `FastLanguageModel.from_pretrained`."
                )

    # Must patch accelerate for Xformers
    # if accelerate_new_send_to_device is not None:
    #     import accelerate.utils.operations
    #     accelerate.utils.operations.send_to_device = accelerate_new_send_to_device
    # pass

    # For newer HF
    kwargs["cache_implementation"] = "dynamic"
    # For num_logits_to_keep
    num_logits_to_keep = kwargs.get("num_logits_to_keep", None)
    logits_to_keep = kwargs.get("logits_to_keep", None)
    if num_logits_to_keep is None and logits_to_keep is None:
        kwargs["num_logits_to_keep"] = 1

    # Remove token_type_ids
    kwargs.pop("token_type_ids", None)

    # Check pad_token
    model_eos_token_id = getattr(self.config, "eos_token_id", None)
    if model_eos_token_id is not None and hasattr(model_eos_token_id, "__iter__"):
        model_eos_token_id = model_eos_token_id[0]

    kwargs["pad_token_id"] = kwargs.pop("pad_token_id", model_eos_token_id)

    # Mixed precision autocast
    with (
        _get_inference_mode_context_manager(self),
        torch.autocast(device_type = DEVICE_TYPE_TORCH, dtype = dtype),
    ):
        output = self._old_generate(*args, **kwargs)

    # Return accelerate back
    # if accelerate_new_send_to_device is not None:
    #     accelerate.utils.operations.send_to_device = accelerate_old_send_to_device
    # pass

    if restore_training_mode:
        FastLlamaModel.for_training(self)

    return output