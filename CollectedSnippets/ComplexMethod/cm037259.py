def apply(self, logits: torch.Tensor) -> torch.Tensor:
        if not self.is_enabled or not self._state:
            return logits

        batch_size = logits.size(0)
        self.mask[:batch_size] = False

        for i in range(batch_size):
            state = self._state.get(i)
            if state and state["in_end"]:
                self.mask[i] = True
                self.force_token_ids[i] = self.reasoning_end_token_ids[
                    state["end_count"]
                ]

        # Check in CPU first not to sync with GPU
        has_active_thinking = any(
            state.get("in_end", False) for state in self._state.values()
        )

        if has_active_thinking:
            current_mask = self.mask[:batch_size]
            active_indices = current_mask.nonzero(as_tuple=False).view(-1)
            if len(active_indices) > 0:
                force_tokens = self.force_token_ids[active_indices]
                # Apply a large value for the end thinking token id index
                logits[active_indices, force_tokens] = 1e9

        return logits