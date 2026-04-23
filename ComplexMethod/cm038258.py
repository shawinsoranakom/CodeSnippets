def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        params_dict = dict(self.named_parameters())
        loaded_params: set[str] = set()

        weights_map = {}

        for name, loaded_weight in weights:
            name = name.replace("medusa_heads.", "")

            if name == "token_map":
                if self.truncated_vocab_size < self.orig_vocab_size:
                    self.token_map = nn.Parameter(loaded_weight, requires_grad=False)
            elif name in params_dict:
                weights_map[name] = loaded_weight
            elif (
                getattr(self.config, "original_lm_head", False)
                and name == "lm_heads.0.weight"
            ):
                weights_map["lm_head.weight"] = loaded_weight

        for name, loaded_weight in weights_map.items():
            if (
                "lm_head" in name
                and self.token_map is not None
                and loaded_weight.shape[0] > self.token_map.shape[0]
            ):
                loaded_weight = loaded_weight[self.token_map]

            param = params_dict[name]
            weight_loader = getattr(param, "weight_loader", default_weight_loader)
            weight_loader(param, loaded_weight)
            loaded_params.add(name)

        if self.token_map is not None:
            self.token_map.to(device=self.lm_heads[0].weight.device)

        assert (self.truncated_vocab_size == self.orig_vocab_size) or (
            self.token_map is not None
        )

        return loaded_params