def new_init(self, *args, **kwargs):
        config_arg = None
        if len(args) >= 2:
            config_arg = args[1]
        else:
            config_arg = kwargs.get("args")

        # Check if model type is unsupported for padding_free
        model = kwargs.get("model")
        is_unsupported_model = False
        is_vlm = False
        if model is not None:
            model_config = getattr(model, "config", None)
            if model_config is not None:
                model_types = get_transformers_model_type(model_config)
                # Blocklist: models that don't work correctly with padding_free
                is_unsupported_model = any(
                    x in PADDING_FREE_BLOCKLIST for x in model_types
                )

                # Check if VLM
                architectures = getattr(model_config, "architectures", None)
                if architectures is None:
                    architectures = []
                is_vlm = any(
                    x.endswith("ForConditionalGeneration") for x in architectures
                )
                is_vlm = is_vlm or hasattr(model_config, "vision_config")

        processing_class = kwargs.get("processing_class") or kwargs.get("tokenizer")
        data_collator = kwargs.get("data_collator")

        # We also disable vision language models for padding free collators
        blocked = (
            (data_collator is not None)
            or isinstance(processing_class, ProcessorMixin)
            or is_vlm
            or is_unsupported_model
            or (
                os.environ.get("UNSLOTH_RETURN_LOGITS", "0") == "1"
            )  # Disable padding free on forced logits
        )
        requested_pack = bool(getattr(config_arg, "packing", False))
        if blocked:
            if hasattr(config_arg, "packing"):
                setattr(config_arg, "packing", False)
            if hasattr(config_arg, "padding_free"):
                setattr(config_arg, "padding_free", False)

        if blocked and requested_pack:
            reason = "custom data collator"
            if data_collator is None and isinstance(processing_class, ProcessorMixin):
                reason = "processor-based model"
            elif is_vlm:
                reason = "vision-language model"
            elif is_unsupported_model:
                reason = f"unsupported model type(s): {', '.join(model_types)}"
            message = "Unsloth: Sample packing skipped " f"({reason} detected)."
            print(message)

        packing_active = False
        if _should_pack(config_arg) and not blocked:
            configure_sample_packing(config_arg)
            packing_active = True
            logger.info("Unsloth: Sample packing enabled for SFTTrainer instance.")

        # Resolve padding_free: None (default) = auto-enable unless env-disabled or packing
        auto_padding_free_active = False
        padding_free_requested = getattr(config_arg, "padding_free", None) is True
        if not blocked:
            if padding_free_requested:
                configure_padding_free(config_arg)
            elif _should_auto_padding_free(config_arg):
                configure_padding_free(config_arg)
                auto_padding_free_active = True
                logger.info(
                    "Unsloth: Padding-free batching auto-enabled for SFTTrainer instance."
                )

        try:
            original_init(self, *args, **kwargs)
        except ValueError as exc:
            if packing_active and _should_skip_auto_packing_error(exc):
                logger.info(
                    "Unsloth: Auto sample packing failed because trainer reported an incompatible setup (%s).",
                    exc,
                )
                _disable_sample_packing(config_arg)
                packing_active = False
                original_init(self, *args, **kwargs)
            else:
                raise

        trainer_args = getattr(self, "args", None)
        trainer_packing = bool(trainer_args and getattr(trainer_args, "packing", False))
        trainer_padding_free = bool(
            trainer_args and getattr(trainer_args, "padding_free", False)
        )

        if blocked and trainer_args is not None:
            # Mirror the block on the trainer args to avoid re-enabling later
            setattr(trainer_args, "packing", False)
            setattr(trainer_args, "padding_free", False)

        if (
            not blocked
            and trainer_packing
            and (packing_active or _should_pack(trainer_args))
        ):
            enable_sample_packing(self.model, self)
            print(
                "🦥 Unsloth: Packing enabled - training is >2x faster and uses less VRAM!"
            )
        elif not blocked and trainer_padding_free:
            enable_padding_free_metadata(self.model, self)
            message = (
                "🦥 Unsloth: Padding-free auto-enabled, enabling faster training."
                if auto_padding_free_active
                else "🦥 Unsloth: Padding-free enabled, enabling faster training."
            )
            print(message)