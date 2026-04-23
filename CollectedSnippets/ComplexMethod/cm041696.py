def __call__(self, features: list[dict[str, Any]]) -> dict[str, "torch.Tensor"]:
        features = super().__call__(features)
        has_dummy_image = features.pop("has_dummy_image", False)
        if self.block_diag_attn and self.attn_implementation != "flash_attention_2":
            features["attention_mask"] = prepare_4d_attention_mask(features["attention_mask"], self.compute_dtype)

        if self.neat_packing and self.attn_implementation == "flash_attention_2": # FIXME compatibility fa3/fa4
            assert features["input_ids"].shape[0] == 1, "bsz should be 1 for neat packing"
            if not has_dummy_image:
                self._unpad_packed_features(features)

            features["attention_mask"] = None  # let transformers handle causal packed mask.

        for key, value in features.items():  # cast data dtype for paligemma
            if torch.is_tensor(value) and torch.is_floating_point(value):
                features[key] = value.to(self.compute_dtype)

        return features