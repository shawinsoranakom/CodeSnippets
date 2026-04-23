def _unpad_packed_features(features: dict[str, Any]) -> None:
        r"""Trim padded positions for packed FA2 batches."""
        attention_mask = features.get("attention_mask")
        if not torch.is_tensor(attention_mask) or attention_mask.dim() != 2 or attention_mask.size(0) != 1:
            return

        seq_len = attention_mask.size(1)
        non_padding_indices = torch.nonzero(attention_mask[0] != 0, as_tuple=False).flatten()
        if non_padding_indices.numel() == seq_len:
            return

        keys_on_seq_dim_1 = {"input_ids", "labels", "attention_mask", "token_type_ids"}
        for key, value in list(features.items()):
            if not torch.is_tensor(value):
                continue

            if key == "position_ids" and value.size(-1) == seq_len:
                features[key] = value.index_select(-1, non_padding_indices)
            elif key == "cross_attention_mask" and value.dim() >= 2 and value.size(0) == 1 and value.size(1) == seq_len:
                features[key] = value.index_select(1, non_padding_indices)
            elif key in keys_on_seq_dim_1 and value.dim() == 2 and value.size(0) == 1 and value.size(1) == seq_len:
                features[key] = value.index_select(1, non_padding_indices)