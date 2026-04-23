def post_patch_model(
        model,
        use_gradient_checkpointing = True,
        trust_remote_code = False,
        model_type = None,
        tokenizer = None,
        float32_mixed_precision = None,
    ):
        full_finetuning = os.environ.get("UNSLOTH_ENABLE_FULL_FINETUNING", "0") == "1"

        if type(float32_mixed_precision) is bool:
            # Respect whatever it was set before
            pass
        else:
            float32_mixed_precision = True
            if (
                _get_dtype(dtype_from_config(model.config)) == torch.bfloat16
                and full_finetuning
            ):
                # Use bfloat16 precision for full finetuning
                float32_mixed_precision = False

        # VLMs can hit DDP "marked ready twice" with re-entrant checkpointing.
        # See: https://github.com/unslothai/unsloth/issues/3713.
        use_reentrant = not is_distributed()
        if not use_reentrant:
            # Under DDP, avoid the offloaded/re-entrant checkpoint patch.
            unpatch_unsloth_gradient_checkpointing()
            unpatch_unsloth_smart_gradient_checkpointing()
            # Force native checkpoint to default to non-reentrant for downstream calls.
            _orig_checkpoint = torch_checkpoint.checkpoint

            def _nonre_checkpoint(function, *args, **kwargs):
                kwargs["use_reentrant"] = False
                return _orig_checkpoint(function, *args, **kwargs)

            torch_checkpoint.checkpoint = _nonre_checkpoint
            hf_modeling_utils.checkpoint = _nonre_checkpoint

        model = prepare_model_for_training(
            model,
            use_gradient_checkpointing = use_gradient_checkpointing,
            use_reentrant = use_reentrant,
            full_finetuning = full_finetuning,
            train_layernorms = full_finetuning,
            train_embedding = full_finetuning,
            train_lm_head = full_finetuning,
            float32_mixed_precision = float32_mixed_precision,
            patch_modules_to_save = True,
        )

        # Gemma3N audio conformer processes variable-length audio tensors
        # that cause stride mismatches in AOT autograd compiled backward
        # when non-reentrant checkpointing is used. The notebook or TRL
        # may override gradient_checkpointing_kwargs with use_reentrant=False
        # after this point, so we intercept gradient_checkpointing_enable
        # to always force use_reentrant=True for Gemma3N.
        _model_type = getattr(getattr(model, "config", None), "model_type", "") or ""
        if "gemma3n" in _model_type.lower() or "gemma4" in _model_type.lower():
            _original_gc_enable = model.gradient_checkpointing_enable

            def _gc_enable_reentrant(**kwargs):
                gc_kwargs = kwargs.get("gradient_checkpointing_kwargs", {}) or {}
                gc_kwargs["use_reentrant"] = True
                kwargs["gradient_checkpointing_kwargs"] = gc_kwargs
                return _original_gc_enable(**kwargs)

            model.gradient_checkpointing_enable = _gc_enable_reentrant

        from transformers.trainer import Trainer

        if (
            Trainer._inner_training_loop.__name__ != "_fast_inner_training_loop"
            and trust_remote_code == False
        ):
            raise RuntimeError("Unsloth: Unsuccessfully patched inner_training_loop")
        patch_saving_functions(model, vision = True)

        # Patch tokenizer to pad to the left
        m = model
        while hasattr(m, "model"):
            if hasattr(m, "_saved_temp_tokenizer"):
                if hasattr(m._saved_temp_tokenizer, "tokenizer"):
                    m._saved_temp_tokenizer.tokenizer.padding_side = "left"
            # Also set is_loaded_in_8bit to disable incorrect DDP
            m.is_loaded_in_8bit = True if not full_finetuning else False
            m = m.model
        if hasattr(m, "_saved_temp_tokenizer"):
            if hasattr(m._saved_temp_tokenizer, "tokenizer"):
                m._saved_temp_tokenizer.tokenizer.padding_side = "left"
        # Also set is_loaded_in_8bit to disable incorrect DDP
        m.is_loaded_in_8bit = True if not full_finetuning else False

        # Clear deleted GPU items
        for _ in range(3):
            gc.collect()
            if DEVICE_TYPE in ("cuda", "hip"):
                torch.cuda.empty_cache()
            elif DEVICE_TYPE == "xpu":
                torch.xpu.empty_cache()
        # Add for_inference and for_training
        model.for_training = functools.partial(FastBaseModel.for_training, model)
        model.for_inference = functools.partial(FastBaseModel.for_inference, model)
        m = model
        while hasattr(m, "model"):
            m.for_training = functools.partial(FastBaseModel.for_training, m)
            m.for_inference = functools.partial(FastBaseModel.for_inference, m)
            m = m.model
        # Set weight[padding_idx] = 0 for embeddings that are NOT tied with the
        # lm_head. When weights are tied, zeroing the padding row also zeros
        # the corresponding lm_head row, forcing logit = 0 for the pad token.
        # Only do this if tokenizer is defined since eos_token == pad_token sometimes!
        pad_token_id = getattr(tokenizer, "pad_token_id", None)
        lm_head = getattr(model, "lm_head", None)
        lm_head_weight = (
            getattr(lm_head, "weight", None) if lm_head is not None else None
        )
        if (
            tokenizer is not None
            and getattr(tokenizer, "eos_token_id", None) != pad_token_id
        ):
            with torch.no_grad():
                for name, module in model.named_modules():
                    if type(module) is torch.nn.Embedding:
                        if (
                            getattr(module, "weight", None) is not None
                            and getattr(module, "padding_idx", None) is not None
                        ):
                            if (
                                module.padding_idx == pad_token_id
                                and module.padding_idx < module.weight.shape[0]
                            ):
                                # Skip if tied to lm_head
                                if (
                                    lm_head_weight is not None
                                    and module.weight.data_ptr()
                                    == lm_head_weight.data_ptr()
                                ):
                                    continue
                                module.weight[module.padding_idx] = 0
        return model