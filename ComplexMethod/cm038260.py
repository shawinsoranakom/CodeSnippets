def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]):
        if not hasattr(self, "mlm_head"):
            cfg = self.model.config
            self.mlm_head = BertMLMHead(
                hidden_size=cfg.hidden_size,
                vocab_size=cfg.vocab_size,
                layer_norm_eps=getattr(cfg, "layer_norm_eps", 1e-12),
            )

        def _strip(name: str) -> str:
            for p in ("model.", "bert."):
                if name.startswith(p):
                    name = name[len(p) :]
            return name

        weights_list = list(weights)
        model_side: list[tuple[str, torch.Tensor]] = []
        mlm_side: list[tuple[str, torch.Tensor]] = []

        for k, w in weights_list:
            name = _strip(k)
            if name.startswith("cls.predictions."):
                mlm_side.append((name, w))
            else:
                model_side.append((name, w))

        loaded: set[str] = set()
        loaded_model = self.model.load_weights(model_side)
        loaded.update({"model." + n for n in loaded_model})

        if mlm_side:
            name_map = {
                "cls.predictions.transform.dense.weight": "mlm_head.dense.weight",
                "cls.predictions.transform.dense.bias": "mlm_head.dense.bias",
                ("cls.predictions.transform.LayerNorm.weight"): (
                    "mlm_head.layer_norm.weight"
                ),
                ("cls.predictions.transform.LayerNorm.bias"): (
                    "mlm_head.layer_norm.bias"
                ),
                "cls.predictions.decoder.weight": "mlm_head.decoder.weight",
                "cls.predictions.decoder.bias": "mlm_head.decoder.bias",
            }
            remapped = [(name_map[n], w) for n, w in mlm_side if n in name_map]
            if remapped:
                loaded_mlm = AutoWeightsLoader(self).load_weights(remapped)
                loaded.update(loaded_mlm)

        return loaded