def _patched_enable_input_require_grads(self):
        def make_inputs_require_grads(module, input, output):
            output.requires_grad_(True)

        hooks = []
        seen_modules = set()

        for module in self.modules():
            if not (
                isinstance(module, PreTrainedModel)
                and hasattr(module, "get_input_embeddings")
            ):
                continue

            try:
                input_embeddings = module.get_input_embeddings()
            except NotImplementedError:
                # Vision models may not implement get_input_embeddings - skip them
                # For GLM V4.6 for example, this skips only `self.visual`
                continue

            if input_embeddings is None:
                continue

            embedding_id = id(input_embeddings)
            if embedding_id in seen_modules:
                continue

            seen_modules.add(embedding_id)
            hooks.append(
                input_embeddings.register_forward_hook(make_inputs_require_grads)
            )

        self._require_grads_hooks = hooks
        if hooks:
            self._require_grads_hook = hooks[0]