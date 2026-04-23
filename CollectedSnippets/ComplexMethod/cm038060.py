def _load_colbert_weights(
        self,
        weights: Iterable[tuple[str, torch.Tensor]],
        colbert_weight_names: tuple[str, ...] = (
            "linear.weight",
            "colbert_linear.weight",
        ),
    ) -> tuple[list[tuple[str, torch.Tensor]], set[str]]:
        """Separate and load ColBERT projection weights.

        Scans *weights* for entries whose name ends with one of
        *colbert_weight_names*.  The matching weight is loaded into
        ``self.colbert_linear`` (creating it first if ``colbert_dim`` was
        not known at init time).

        Args:
            weights: Iterable of ``(name, tensor)`` weight pairs.
            colbert_weight_names: Suffixes that identify the ColBERT linear
                weight.

        Returns:
            ``(remaining_weights, loaded_names)`` — the weights that were
            **not** consumed and the set of names that were loaded.
        """
        weights_list = list(weights)
        other_weights: list[tuple[str, torch.Tensor]] = []
        colbert_weight: tuple[str, torch.Tensor] | None = None

        for name, weight in weights_list:
            if any(name.endswith(cw) for cw in colbert_weight_names):
                colbert_weight = (name, weight)
            else:
                other_weights.append((name, weight))

        loaded: set[str] = set()
        if colbert_weight is not None:
            _name, weight = colbert_weight
            if weight.dim() == 2:
                # Infer colbert_dim from weight shape if not set
                if self.colbert_dim is None:
                    self.colbert_dim = weight.shape[0]
                    self.colbert_linear = self._build_colbert_linear()
                    # Update the pooler's projector
                    if hasattr(self, "pooler") and hasattr(self.pooler, "head"):
                        self.pooler.head.projector = self.colbert_linear

                assert self.colbert_linear is not None
                # Move to same device as model
                if hasattr(self, "model"):
                    device = next(self.model.parameters()).device
                    self.colbert_linear.to(device)

                weight = weight.to(self.colbert_linear.weight.device)
                self.colbert_linear.weight.data.copy_(weight)
                loaded.add("pooler.head.projector.weight")

        return other_weights, loaded