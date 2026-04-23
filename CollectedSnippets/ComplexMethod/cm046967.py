def for_training(model, use_gradient_checkpointing = True):
        if not hasattr(model, "parameters"):
            raise TypeError(
                "Unsloth: I think you're passing a tokenizer, not the model to for_training!"
            )

        # Delete all fast inference loras
        for param in model.parameters():
            if hasattr(param, "_fast_lora"):
                del param._fast_lora

        def _for_training(m):
            if hasattr(m, "gradient_checkpointing"):
                m.gradient_checkpointing = use_gradient_checkpointing
            if hasattr(m, "training"):
                m.training = True
            # Pad tokenizer to the left
            if hasattr(m, "_saved_temp_tokenizer"):
                m._saved_temp_tokenizer.padding_side = "right"
            # Set a flag for generation!
            if hasattr(m, "_flag_for_generation"):
                try:
                    # Weirdly sometimes cannot succeed so do a try except
                    del m._flag_for_generation
                except:
                    pass

        m = model
        while hasattr(m, "model"):
            _for_training(m)
            m = m.model
        _for_training(m)
        model.train()  # to turn on training on modules deeper in

        # Since transformers 4.53, must turn on explicitly
        for module in model.modules():
            if hasattr(module, "gradient_checkpointing"):
                module.gradient_checkpointing = use_gradient_checkpointing

        # Also re-enable training for embeddings for NEFTune
        if hasattr(model, "get_input_embeddings"):
            embeddings = model.get_input_embeddings()
            if hasattr(embeddings, "training"):
                embeddings.training = True
        if hasattr(model, "get_output_embeddings"):
            embeddings = model.get_output_embeddings()
            if hasattr(embeddings, "training"):
                embeddings.training = True
        # Can re-enable not returning logits
        os.environ["UNSLOTH_RETURN_LOGITS"] = "0"
        # Turn off skip guards and set stance to default
        if torch_compiler_set_stance is not None:
            torch_compiler_set_stance(stance = "default", skip_guard_eval_unsafe = False)
        return model