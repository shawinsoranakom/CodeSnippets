def _fast_prepare_inputs_for_generation(
    self,
    input_ids,
    attention_mask = None,
    inputs_embeds = None,
    **kwargs,
):
    past_key_values = kwargs.get("past_key_values", None)
    original_attention_mask = attention_mask

    # Handle inputs_embeds - only use on FIRST generation step (no cache)
    # This fixes GitHub issue #3798: inputs_embeds was ignored
    use_inputs_embeds = inputs_embeds is not None and past_key_values is None

    if input_ids is not None and input_ids.numel() > 0:
        bs, seq_length = input_ids.shape
        device = input_ids.device
    elif inputs_embeds is not None:
        bs, seq_length, _ = inputs_embeds.shape
        device = inputs_embeds.device
    else:
        bs, seq_length = 1, 0
        device = "cuda" if torch.cuda.is_available() else "cpu"

    if past_key_values is not None:
        # Check for uninitialized DynamicCache
        if len(past_key_values) == 0:
            past_key_values = None
            kwargs["past_key_values"] = None
            use_inputs_embeds = inputs_embeds is not None
        # New since 4.56
        elif (
            hasattr(past_key_values, "get_seq_length")
            and past_key_values.get_seq_length() == 0
        ):
            past_key_values = None
            kwargs["past_key_values"] = None
            use_inputs_embeds = inputs_embeds is not None
        else:
            if input_ids is not None and input_ids.numel() > 0:
                bs = input_ids.shape[0]
                input_ids = input_ids[:, [-1]]
                device = input_ids.device
                seq_length = 1
            elif inputs_embeds is not None:
                bs, seq_length, _ = inputs_embeds.shape
                device = inputs_embeds.device
            else:
                bs, seq_length = 1, 0
                device = "cuda" if torch.cuda.is_available() else "cpu"

            if hasattr(past_key_values, "get_seq_length"):
                past_len = int(past_key_values.get_seq_length())
            else:
                # legacy tuple cache: (layer, (K,V))
                past_len = int(past_key_values[0][0].shape[-2])

            max_cache_len = None
            if hasattr(past_key_values, "get_max_cache_shape"):
                m = past_key_values.get_max_cache_shape()
                max_cache_len = int(m) if m is not None and m > 0 else None
            elif hasattr(past_key_values, "get_max_length"):
                m = past_key_values.get_max_length()
                max_cache_len = int(m) if m is not None else None

            # ensure cache_position
            cache_position = kwargs.get("cache_position", None)
            if cache_position is None:
                kwargs["cache_position"] = torch.arange(
                    past_len,
                    past_len + seq_length,
                    device = device,
                    dtype = torch.long,
                )
            else:
                if (
                    hasattr(cache_position, "device")
                    and cache_position.device != device
                ):
                    kwargs["cache_position"] = cache_position.to(device)

            # Get to the base model
            base_model = self
            if hasattr(base_model, "base_model_prefix"):
                base_model = getattr(base_model, base_model.base_model_prefix)

            if hasattr(
                base_model, "_prepare_4d_causal_attention_mask_with_cache_position"
            ):
                if not hasattr(base_model, "_unsloth_mask_needs_device"):

                    def _check_needs_device(fn) -> bool:
                        try:
                            sig = inspect.signature(inspect.unwrap(fn))
                            return "device" in sig.parameters
                        except:
                            # transformers <= 4.51.3 includes device arg but > 4.51.3 does not
                            return transformers_version < Version("4.52.0")

                    base_model._unsloth_mask_needs_device = _check_needs_device(
                        base_model._prepare_4d_causal_attention_mask_with_cache_position
                    )

                if max_cache_len is not None:
                    target_length = max_cache_len
                elif (
                    original_attention_mask is not None
                    and original_attention_mask.dim() == 2
                ):
                    target_length = original_attention_mask.shape[-1]
                else:
                    target_length = past_len + seq_length

                mask_kwargs = {
                    "sequence_length": seq_length,
                    "target_length": target_length,
                    "dtype": self.dtype,
                    "cache_position": kwargs["cache_position"],
                    "batch_size": bs,
                    "config": self.config,
                    "past_key_values": past_key_values,
                }
                if base_model._unsloth_mask_needs_device:
                    mask_kwargs["device"] = device

                attention_mask = (
                    base_model._prepare_4d_causal_attention_mask_with_cache_position(
                        attention_mask,
                        **mask_kwargs,
                    )
                )
            else:
                if transformers_version <= Version("4.52.4"):
                    logger.warning_once(
                        f"{self.__class__.__name__} has no `_prepare_4d_causal_attention_mask_with_cache_position` method "
                        "defined in its base modeling class. Compiled forward passes will be sub-optimal. If you're "
                        "writing code, see Llama for an example implementation. If you're a user, please report this "
                        "issue on GitHub."
                    )

    if kwargs.get("position_ids", None) is None:
        if original_attention_mask is not None and original_attention_mask.dim() == 2:
            position_ids = original_attention_mask.long().cumsum(-1) - 1
            position_ids.masked_fill_(original_attention_mask == 0, 1)
            position_ids = position_ids[:, -seq_length:]
            kwargs["position_ids"] = position_ids
        elif kwargs.get("cache_position", None) is not None:
            cp = kwargs["cache_position"]
            if cp.dim() == 1:
                cp = cp.unsqueeze(0).expand(bs, -1)
            kwargs["position_ids"] = cp

    result = {
        "attention_mask": attention_mask,
        **kwargs,
    }
    if use_inputs_embeds:
        result["inputs_embeds"] = inputs_embeds
        result["input_ids"] = None
    else:
        result["input_ids"] = input_ids
    return result