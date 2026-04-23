def enable_input_require_grads(self):
        """
        Enables the gradients for the input embeddings. This is useful for fine-tuning adapter weights while keeping
        the model weights fixed.
        """

        def make_inputs_require_grads(module, input, output):
            output.requires_grad_(True)

        hooks = []
        seen_modules = set()
        found_embeddings = False

        for module in self.modules():
            if not (isinstance(module, PreTrainedModel) and hasattr(module, "get_input_embeddings")):
                continue

            try:
                input_embeddings = module.get_input_embeddings()
            except NotImplementedError:
                continue

            if input_embeddings is None or not hasattr(input_embeddings, "register_forward_hook"):
                continue

            embedding_id = id(input_embeddings)
            if embedding_id in seen_modules:
                continue

            seen_modules.add(embedding_id)
            hooks.append(input_embeddings.register_forward_hook(make_inputs_require_grads))
            found_embeddings = True

        self._require_grads_hooks = hooks
        if hooks:
            # for BC
            self._require_grads_hook = hooks[0]
        if not found_embeddings:
            logger.warning_once(
                f"{self.__class__.__name__} does not expose input embeddings. Gradients cannot flow back to the token "
                "embeddings when using adapters or gradient checkpointing. Override `get_input_embeddings` to fully "
                "support those features, or set `_input_embed_layer` to the attribute name that holds the embeddings."
            )