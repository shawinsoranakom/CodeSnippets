def for_inference(model):
        if not hasattr(model, "parameters"):
            raise TypeError(
                "Unsloth: I think you're passing a tokenizer, not the model to for_inference!"
            )

        def _for_inference(m):
            if hasattr(m, "gradient_checkpointing"):
                m.gradient_checkpointing = False
            if hasattr(m, "training"):
                m.training = False
            # Pad tokenizer to the left
            if hasattr(m, "_saved_temp_tokenizer"):
                m._saved_temp_tokenizer.padding_side = "left"
            # Set a flag for generation!
            m._flag_for_generation = True

        m = model
        while hasattr(m, "model"):
            _for_inference(m)
            m = m.model
        _for_inference(m)
        model.eval()  # to turn off training on modules deeper in

        # Since transformers 4.53, must turn off explicitly
        for module in model.modules():
            if hasattr(module, "gradient_checkpointing"):
                module.gradient_checkpointing = False

        # Also disable training for embeddings for NEFTune
        if hasattr(model, "get_input_embeddings"):
            embeddings = model.get_input_embeddings()
            if hasattr(embeddings, "training"):
                embeddings.training = False
        if hasattr(model, "get_output_embeddings"):
            embeddings = model.get_output_embeddings()
            if hasattr(embeddings, "training"):
                embeddings.training = False
        # Must disable returning hidden states in the case for GRPO
        os.environ["UNSLOTH_RETURN_HIDDEN_STATES"] = "0"
        # Must enable returning logits
        os.environ["UNSLOTH_RETURN_LOGITS"] = "1"
        # Turn off skip guards and set stance to default
        if torch_compiler_set_stance is not None:
            torch_compiler_set_stance(stance = "default", skip_guard_eval_unsafe = False)
        return model