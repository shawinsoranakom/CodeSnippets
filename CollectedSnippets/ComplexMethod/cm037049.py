def update_from_generation_config(
        self,
        generation_config: dict[str, Any],
        eos_token_id: int | None = None,
    ) -> None:
        """Update if there are non-default values from generation_config"""
        if not self.ignore_eos:
            self._eos_token_id = eos_token_id

        if eos_token_id is not None:
            # Add the eos token id into the sampling_params to support
            # min_tokens processing.
            self._all_stop_token_ids.add(eos_token_id)

        # Update eos_token_id for generation
        if (eos_ids := generation_config.get("eos_token_id")) is not None:
            # it can be either int or list of int
            eos_ids = {eos_ids} if isinstance(eos_ids, int) else set(eos_ids)
            if eos_token_id is not None:
                # We don't need to include the primary eos_token_id in
                # stop_token_ids since it's handled separately for stopping
                # purposes.
                eos_ids.discard(eos_token_id)
            if eos_ids:
                self._all_stop_token_ids.update(eos_ids)
                if not self.ignore_eos:
                    assert self.stop_token_ids is not None
                    eos_ids.update(self.stop_token_ids)
                    self.stop_token_ids = list(eos_ids)