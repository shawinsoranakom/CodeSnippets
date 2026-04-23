def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        """Load weights with special handling for ColQwen3 projection layer."""
        weights_list = list(weights)
        proj_weights: list[tuple[str, torch.Tensor]] = []
        model_weights: list[tuple[str, torch.Tensor]] = []

        # Scan all weight names to determine if re-prefixing is needed.
        # OpenSearch-AI models have unprefixed weights ("language_model.*",
        # "visual.*") that need "model." added so hf_to_vllm_mapper can
        # process them. Only re-prefix if ALL backbone weights are
        # unprefixed (no "vlm." or "model." prefix found).
        has_unprefixed = any(
            name.startswith("language_model.") or name.startswith("visual.")
            for name, _ in weights_list
        )
        has_prefixed = any(
            name.startswith("vlm.") or name.startswith("model.")
            for name, _ in weights_list
        )
        needs_reprefix = has_unprefixed and not has_prefixed

        for name, weight in weights_list:
            if self._is_proj_weight(name):
                proj_weights.append((name, weight))
            else:
                if needs_reprefix and not self._is_proj_weight(name):
                    name = "model." + name
                model_weights.append((name, weight))

        loader = AutoWeightsLoader(self)
        loaded = loader.load_weights(model_weights, mapper=self.hf_to_vllm_mapper)

        if proj_weights:
            model_dtype = next(self.language_model.parameters()).dtype
            model_device = next(self.language_model.parameters()).device

            for name, weight in proj_weights:
                if self.embed_dim is None and "weight" in name:
                    self.embed_dim = weight.shape[0]
                    has_bias = any("bias" in n for n, _ in proj_weights)
                    self.custom_text_proj = nn.Linear(
                        self._proj_hidden_size,
                        self.embed_dim,
                        bias=has_bias,
                        dtype=model_dtype,
                    )
                    self.custom_text_proj.to(model_device)

                if self.custom_text_proj is not None:
                    param_name = name.split(".")[-1]
                    param = getattr(self.custom_text_proj, param_name, None)
                    if param is not None:
                        weight = weight.to(device=param.device, dtype=param.dtype)
                        default_weight_loader(param, weight)
                        loaded.add(f"custom_text_proj.{param_name}")

        return loaded