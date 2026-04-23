def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]):
        other_weights, colbert_loaded = self._load_colbert_weights(weights)

        # Strip "model." prefix added by the embedding adapter
        model_weights = [
            (n[len("model.") :] if n.startswith("model.") else n, w)
            for n, w in other_weights
        ]
        loaded_model = self.model.load_weights(model_weights)
        loaded = {f"model.{name}" for name in loaded_model} | colbert_loaded

        # When the ST projector was auto-loaded during init
        # (not from the main checkpoint), mark its params as loaded
        # so the weight validator doesn't complain.
        if hasattr(self.pooler, "head"):
            head = self.pooler.head
            projector = getattr(head, "projector", None)
            if projector is not None and isinstance(projector, nn.Module):
                for name, _ in projector.named_parameters():
                    loaded.add(f"pooler.head.projector.{name}")

        return loaded