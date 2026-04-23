def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]):
        model_weights = {}
        includes_draft_id_mapping = False
        includes_embed_tokens = False
        includes_mask_hidden = False
        for name, loaded_weight in weights:
            if "t2d" in name:
                continue
            if "d2t" in name:
                name = name.replace("d2t", "draft_id_to_target_id")
                includes_draft_id_mapping = True
            elif "mask_hidden" in name:
                # Load mask_hidden directly into buffer
                if not self.use_parallel_drafting:
                    logger.warning(
                        "mask_hidden found in weights but "
                        "model is not configured for parallel drafting. "
                        "Skipping loading mask_hidden."
                    )
                    continue
                self.mask_hidden.copy_(loaded_weight.view(1, -1))
                includes_mask_hidden = True
                continue
            elif "lm_head" not in name:
                name = "model." + name
            if "embed_tokens" in name:
                includes_embed_tokens = True
            model_weights[name] = loaded_weight
            process_eagle_weight(self, name)

        if not includes_mask_hidden and self.use_parallel_drafting:
            raise ValueError(
                "mask_hidden not found in weights but "
                "model is configured for parallel drafting. "
                "Please provide mask_hidden in the weights."
            )

        skip_substrs = ["mask_hidden"]
        if not includes_draft_id_mapping:
            skip_substrs.append("draft_id_to_target_id")
        if not includes_embed_tokens:
            skip_substrs.append("embed_tokens")
        if not self.model.use_aux_hidden_state:
            skip_substrs.append("fc.")
        if not self.model.norm_before_fc:
            skip_substrs.append("input_norm.")
        loader = AutoWeightsLoader(
            self,
            skip_prefixes=None,
            skip_substrs=skip_substrs,
        )
        loader.load_weights(model_weights.items())