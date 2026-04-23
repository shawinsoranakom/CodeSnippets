def post_patch(model, tokenizer, correct_dtype = None):
        # Torch.compile fails on embedding matrix??
        # Workaround randomnly fixes it for torch versions < 2.2
        model.model.embed_tokens = torch.nn.Embedding.from_pretrained(
            model.model.embed_tokens.weight
        )
        model.config.update({"unsloth_version": __version__})

        # We also do this for the lm_head
        lm_head = torch.nn.Linear(1, 1, bias = None)
        del lm_head.weight
        lm_head.weight = model.lm_head.weight
        lm_head.in_features = lm_head.weight.shape[1]
        lm_head.out_features = lm_head.weight.shape[0]
        model.lm_head = lm_head

        # Granite has tied weights! This means lm_head == embed_tokens
        if (
            model.model.embed_tokens.weight.data_ptr()
            != model.lm_head.weight.data_ptr()
        ):
            lm_head = torch.nn.Linear(1, 1, bias = None)
            del lm_head.weight
            lm_head.weight = model.model.embed_tokens.weight
            lm_head.in_features = lm_head.weight.shape[1]
            lm_head.out_features = lm_head.weight.shape[0]
            model.lm_head = lm_head

        # Also patch all dtypes - BnB seems to not allocate the correct type?
        # BnB default dtype seems to be float16!
        correct_dtype = lm_head.weight.dtype

        for name, module in model.named_modules():
            if isinstance(module, (Bnb_Linear4bit, Peft_Linear4bit)):
                weight = module.weight
                quant_state = weight.quant_state

                if type(quant_state) is list:
                    # BnB seems to have float16 as default!
                    module.weight.quant_state[2] = (
                        correct_dtype  # Cast to correct dtype
                    )
                else:
                    # https://github.com/TimDettmers/bitsandbytes/pull/763/files
                    quant_state.dtype = correct_dtype
            # Downcast RoPE embedding to correct data type
            if name.endswith("rotary_emb") or hasattr(module, "cos_cached"):
                if hasattr(module, "cos_cached") and (
                    module.cos_cached.dtype != correct_dtype
                ):
                    module.cos_cached = module.cos_cached.to(correct_dtype)
                    module.sin_cached = module.sin_cached.to(correct_dtype)

                elif hasattr(module, "short_cos_cached") and (
                    module.short_cos_cached.dtype != correct_dtype
                ):
                    module.short_cos_cached = module.short_cos_cached.to(correct_dtype)
                    module.short_sin_cached = module.short_sin_cached.to(correct_dtype)

        # Clear deleted GPU items
        import gc

        for _ in range(3):
            gc.collect()
            torch.cuda.empty_cache()
        return model, tokenizer