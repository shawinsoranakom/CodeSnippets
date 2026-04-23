def unsloth_base_fast_generate(
    self,
    *args,
    **kwargs,
):
    if len(args) != 0:
        input_ids = args[0]
    elif "input_ids" in kwargs:
        input_ids = kwargs["input_ids"]
    elif "input" in kwargs:
        input_ids = kwargs["input"]
    elif "input_features" in kwargs:
        input_ids = kwargs["input_features"]
    elif "input_embeds" in kwargs:
        input_ids = kwargs["input_embeds"]
    elif "inputs" in kwargs:
        input_ids = kwargs["inputs"]
    else:
        key = next(iter(kwargs.keys()))
        if type(kwargs[key]) is not torch.Tensor:
            raise TypeError("Unsloth: You need to pass in input_ids to .generate!")
        input_ids = kwargs[key]
    assert type(input_ids) is torch.Tensor
    bsz = input_ids.shape[0]

    FastBaseModel.for_inference(self)
    dtype = _get_dtype(dtype_from_config(self.config))
    # Handle full float32 cases as config.dtype == torch.float32!
    do_bfloat16_mixed_precision = (
        os.environ.get("UNSLOTH_BFLOAT16_MIXED_PRECISION", "0") == "1"
    )
    if do_bfloat16_mixed_precision:
        dtype = torch.bfloat16

    # Check if VLM
    is_vlm = any(
        x.endswith(("ForConditionalGeneration", "ForVisionText2Text"))
        for x in self.config.architectures
    )
    is_vlm = is_vlm or hasattr(self.config, "vision_config")
    arch = self.config.architectures[0]

    # Remove token_type_ids - WRONG for Gemma 3 since bidirectional attention
    if hasattr(self, "generate") and hasattr(self, "forward"):
        # did not combine with below since self might not have model
        keys = inspect.signature(self.forward).parameters.keys()
        if "token_type_ids" not in keys:
            kwargs.pop("token_type_ids", None)
    # kwargs.pop("token_type_ids", None)

    # VLMs do not allow logits_to_keep
    global NUM_LOGITS_TO_KEEP
    if arch not in NUM_LOGITS_TO_KEEP:
        m = self
        # Find which is needed ie
        # num_logits_to_keep or logits_to_keep
        while hasattr(m, "model"):
            if hasattr(m, "forward"):
                keys = inspect.signature(m.forward).parameters.keys()
                if "num_logits_to_keep" in keys:
                    NUM_LOGITS_TO_KEEP[arch] = "num_logits_to_keep"
                    break
                elif "logits_to_keep" in keys:
                    NUM_LOGITS_TO_KEEP[arch] = "logits_to_keep"
                    break
            m = m.model
        if arch not in NUM_LOGITS_TO_KEEP:
            NUM_LOGITS_TO_KEEP[arch] = None
    key = NUM_LOGITS_TO_KEEP[arch]
    if key is not None and key not in kwargs:
        kwargs[key] = 1

    # Check pad_token
    model_eos_token_id = getattr(self.config, "eos_token_id", None)
    if model_eos_token_id is not None and hasattr(model_eos_token_id, "__iter__"):
        model_eos_token_id = model_eos_token_id[0]

    kwargs["pad_token_id"] = kwargs.pop("pad_token_id", model_eos_token_id)

    # Get pixel values for VLMs
    try:
        kwargs["pixel_values"] = kwargs["pixel_values"].to(dtype)
    except:
        pass
    try:
        kwargs["pixel_values_videos"] = kwargs["pixel_values_videos"].to(dtype)
    except:
        pass

    # Mixed precision autocast
    if os.environ.get("UNSLOTH_FORCE_FLOAT32", "0") == "1":
        autocaster = torch.autocast(device_type = DEVICE_TYPE_TORCH, dtype = torch.float16)
        dtype = torch.float16
    else:
        autocaster = torch.autocast(device_type = DEVICE_TYPE_TORCH, dtype = dtype)
    # Prepare LoRA
    # state_dict = convert_lora_modules(self, dtype = dtype)

    # Set compile dynamic shapes
    torch._dynamo.mark_static(input_ids, 0)
    torch._dynamo.mark_dynamic(input_ids, 1)
    if "attention_mask" in kwargs:
        torch._dynamo.mark_static(kwargs["attention_mask"], 0)
        torch._dynamo.mark_dynamic(kwargs["attention_mask"], 1)
    if "token_type_ids" in kwargs:
        torch._dynamo.mark_static(kwargs["token_type_ids"], 0)
        torch._dynamo.mark_dynamic(kwargs["token_type_ids"], 1)

    # Fix generation_config
    # Use hybrid if sliding window seen, otherwise try static
    cache_implementation = getattr(self.config, "cache_implementation", None)
    if getattr(
        self, "_supports_static_cache", getattr(self, "_can_compile_fullgraph", True)
    ):
        if os.environ.get("UNSLOTH_DISABLE_STATIC_GENERATION", "0") == "0":
            cache_implementation = "static"
        elif Version(transformers_version) < Version("4.56.0.dev0"):
            cache_implementation = None
        else:
            # Should work in latest transformers!
            cache_implementation = "static"
    else:
        cache_implementation = None
    if cache_implementation is not None:
        swa = getattr(
            getattr(self.config, "text_config", self.config), "sliding_window", None
        )
        if (swa == 0 or type(swa) is not int) and (
            getattr(self, "_can_compile_fullgraph", True) is True
        ):
            cache_implementation = "static"
        else:
            if Version(transformers_version) < Version("4.56.0.dev0"):
                cache_implementation = "hybrid"
            else:
                cache_implementation = "static"
    # [TODO] Unsure why static fails
    if do_bfloat16_mixed_precision:
        cache_implementation = None

    if "generation_config" in kwargs:
        kwargs["generation_config"].cache_implementation = cache_implementation
        if cache_implementation is not None:
            kwargs["generation_config"].compile_config = _compile_config
    else:
        kwargs["cache_implementation"] = cache_implementation
        if cache_implementation is not None:
            kwargs["compile_config"] = _compile_config

    # Delete cached Flex Attention masks to reset inference
    for name, module in self.named_modules():
        if hasattr(module, "_flex_attention_cache"):
            try:
                del module._flex_attention_cache
            except:
                pass
        # Solves AttributeError: 'SlidingWindowLayer' object has no attribute 'max_batch_size'
        if hasattr(module, "_cache") and "cache_utils" in str(module._cache.__class__):
            try:
                del module._cache
            except:
                pass

    # DO INFERENCE
    with torch.inference_mode(), autocaster:
        output = self._old_generate(*args, **kwargs)

    # Delete cached Flex Attention masks to reset inference
    for name, module in self.named_modules():
        if hasattr(module, "_flex_attention_cache"):
            try:
                del module._flex_attention_cache
            except:
                pass
        # Solves AttributeError: 'SlidingWindowLayer' object has no attribute 'max_batch_size'
        if hasattr(module, "_cache") and "cache_utils" in str(module._cache.__class__):
            try:
                del module._cache
            except:
                pass

    # FastBaseModel.for_training(self)
    return output