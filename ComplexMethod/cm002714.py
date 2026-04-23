def has_previous_state(self, layer_idx: int | None = None) -> bool:
        """Returns whether the LinearAttention layer at index `layer_idx` has previous state or not."""
        if layer_idx is not None and layer_idx >= len(self.layers):
            return False

        # In this case, use last LinearAttention layer
        if layer_idx is None:
            try:
                layer_idx = next(
                    idx
                    for idx in range(len(self) - 1, -1, -1)
                    if isinstance(self.layers[idx], LinearAttentionCacheLayerMixin)
                )
            except StopIteration:
                raise ValueError(
                    "`has_previous_state` can only be called on LinearAttention layers, and the current Cache seem to "
                    "only contain Attention layers."
                )
        elif not isinstance(self.layers[layer_idx], LinearAttentionCacheLayerMixin):
            raise ValueError(
                f"You called `has_previous_state` on layer index {layer_idx}, but this layer is an Attention layer, which "
                "does not support calling it."
            )

        return self.layers[layer_idx].has_previous_state