def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]):
        weights_list = list(weights)
        model_side: list[tuple[str, torch.Tensor]] = []
        colbert_side: list[tuple[str, torch.Tensor]] = []

        for name, weight in weights_list:
            stripped = name
            # Strip "model." prefix added by the embedding adapter
            if stripped.startswith("model."):
                stripped = stripped[len("model.") :]
            # Strip "roberta." prefix from checkpoint
            if stripped.startswith("roberta."):
                stripped = stripped[len("roberta.") :]

            if stripped in ("linear.weight", "colbert_linear.weight"):
                colbert_side.append(("colbert_linear.weight", weight))
            elif stripped.startswith("pooler."):
                # Skip HF pooler weights (not used in ColBERT)
                continue
            else:
                model_side.append((stripped, weight))

        loaded: set[str] = set()
        loaded_model = self.model.load_weights(model_side)
        loaded.update({"model." + n for n in loaded_model})

        if colbert_side:
            _, colbert_loaded = self._load_colbert_weights(colbert_side)
            loaded.update(colbert_loaded)

        return loaded