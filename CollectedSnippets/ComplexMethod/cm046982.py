def post_patch(model, tokenizer, correct_dtype = None):
        # Gemma does not downcast RoPE
        model, tokenizer = patch_model_and_tokenizer(
            model, tokenizer, downcast_rope = False, correct_dtype = correct_dtype
        )

        # Add 1 to weight
        # return output * (1 + self.weight)
        # https://github.com/huggingface/transformers/blob/main/src/transformers/models/gemma/modeling_gemma.py#L89
        from transformers.models.gemma.modeling_gemma import GemmaRMSNorm

        # Freeze all parameters except LoRA
        # We do this first since += 1 seems to not be liked by requires_grad = True
        for name, param in model.named_parameters():
            if ".lora_A." in name or ".lora_B." in name:
                param.requires_grad_(True)
            else:
                param.requires_grad_(False)

        # Patch RMS Layernorm
        for name, module in model.named_modules():
            if isinstance(module, GemmaRMSNorm):
                # Must be in float32
                # https://github.com/keras-team/keras-nlp/blob/v0.8.2/keras_nlp/models/gemma/rms_normalization.py#L36
                # module = module.to(torch.float32)
                # Leave + 1 to Triton kernel itself
                # module.weight += 1.0 # return output * (1 + self.weight)
                if not hasattr(module, "variance_epsilon"):
                    module.variance_epsilon = (
                        module.eps
                    )  # Gemma doesn't use variance_epsilon

        # Clear deleted GPU items
        import gc

        for _ in range(3):
            gc.collect()
            torch.cuda.empty_cache()
        return model, tokenizer