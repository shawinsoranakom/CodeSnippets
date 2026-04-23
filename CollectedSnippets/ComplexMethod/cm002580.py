def _from_config(cls, config, **kwargs):
        """
        All context managers that the model should be initialized under go here.

        Args:
            dtype (`torch.dtype`, *optional*):
                Override the default `dtype` and load the model under this dtype.
        """
        # For BC on the old `torch_dtype`
        dtype = kwargs.pop("dtype", config.dtype)
        if (torch_dtype := kwargs.pop("torch_dtype", None)) is not None:
            logger.warning_once("`torch_dtype` is deprecated! Use `dtype` instead!")
            # if both kwargs are provided, use `dtype`
            dtype = dtype if dtype != config.dtype else torch_dtype
        if isinstance(dtype, str):
            dtype = getattr(torch, dtype)

        # Set the same `dtype` on all subconfigs to avoid dtype mismatch. When "auto" dtype
        # with nested models, we can't dispatch different dtype per backbone module
        for sub_config_key in config.sub_configs:
            if (sub_config := getattr(config, sub_config_key)) is not None:
                sub_config.dtype = dtype

        # If passing `attn_implementation` as kwargs, respect it (it will be applied recursively on subconfigs)
        if "attn_implementation" in kwargs:
            config._attn_implementation = kwargs.pop("attn_implementation")

        # If passing `experts_implementation` as kwargs, respect it (it will be applied recursively on subconfigs)
        if "experts_implementation" in kwargs:
            config._experts_implementation = kwargs.pop("experts_implementation")

        # Needed if the attn_implementation is an outside `kernels-community` kernel
        allow_all_kernels = kwargs.get("allow_all_kernels", False)

        init_contexts = [apply_patches()]
        if dtype is not None:
            init_contexts.append(local_torch_dtype(dtype, cls.__name__))
        if allow_all_kernels:
            init_contexts.append(allow_all_hub_kernels())

        needs_zero3_init = is_deepspeed_zero3_enabled() and not _is_quantized and not _is_ds_init_called
        if needs_zero3_init:
            logger.info("Detected DeepSpeed ZeRO-3: activating zero.init() for this model")
            # this immediately partitions the model across all gpus, to avoid the overhead in time
            # and memory copying it on CPU or each GPU first
            import deepspeed

            init_contexts.extend(
                [
                    init.no_init_weights(),
                    deepspeed.zero.Init(config_dict_or_path=deepspeed_config()),
                    set_zero3_state(),
                ]
            )

        # Instantiate the model
        with ContextManagers(init_contexts):
            model = cls(config, **kwargs)
            patch_output_recorders(model)

        # Under ZeRO-3, parameters were partitioned into empty tensors during construction,
        # so weight init was suppressed. Re-initialize using the ZeRO-3 variant which gathers
        # each module's parameters before init to avoid OOM on large models.
        if needs_zero3_init:
            from .integrations.deepspeed import initialize_weights_zero3

            initialize_weights_zero3(model)
            model.tie_weights()

        return model