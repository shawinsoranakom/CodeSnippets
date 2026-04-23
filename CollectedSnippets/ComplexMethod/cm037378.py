def _get_eagle3_aux_layers_from_config(self) -> tuple[int, ...] | None:
        """Extract Eagle3 auxiliary layer indices from speculative config.

        These indices specify which hidden states from the base model should
        be used as auxiliary inputs for the Eagle3 drafter model during
        speculative decoding.

        Returns:
            Tuple of layer indices if found in draft model config,
            None otherwise.
        """
        if not (self.speculative_config and self.speculative_config.draft_model_config):
            return None

        hf_config = self.speculative_config.draft_model_config.hf_config

        layer_ids = getattr(hf_config, "eagle_aux_hidden_state_layer_ids", None)
        if not layer_ids:
            dflash_config = getattr(hf_config, "dflash_config", None)
            if dflash_config and isinstance(dflash_config, dict):
                layer_ids = dflash_config.get("target_layer_ids")

        if layer_ids and isinstance(layer_ids, (list, tuple)):
            return tuple(layer_ids)

        return None