def _compute_rope_position_ids_with_packing(
        self,
        features: dict[str, "torch.Tensor"],
        mm_inputs: dict[str, Any],
        packing_params_list: list[dict[str, Any] | None],
        batch_imglens: list[int],
        batch_vidlens: list[int],
        batch_audlens: list[int],
        has_dummy_image: bool,
    ) -> None:
        r"""Compute position_ids and rope_deltas per sample (or per sub-sequence when packed), then merge and validate."""
        bsz = features["input_ids"].size(0)
        seq_len = features["input_ids"].size(1)
        all_position_ids: list[torch.Tensor] = []
        all_rope_deltas: list[torch.Tensor] = []

        if has_dummy_image:
            # for [0, seq_len] = [0, unpadded_length + right_padding_length + fake_input_ids_len + collator_padding_length]
            # FIXME: maybe right_padding_length is large, with improper max_cutoff_len
            unpadded_length = int(features["attention_mask"][0].bool().sum().item())
            right_padding_length = int((packing_params_list[0] or {}).get("right_padding_length") or 0)
            fake_input_padding_length = max(0, seq_len - unpadded_length - right_padding_length)
            dummy_image_right_padding_mrope = torch.zeros((3, bsz, fake_input_padding_length))
            dummy_image_right_padding_attention_mask = torch.zeros((bsz, fake_input_padding_length))
            assert self.tokenizer.padding_side == "right", "padding_side should be right when fake image is injected"
            dummy_mm_inputs = copy.deepcopy(mm_inputs)

        for sample_idx in range(bsz):
            sample_packing = (packing_params_list[sample_idx] or {}) if sample_idx < len(packing_params_list) else {}
            sequence_boundaries = sample_packing.get("sequence_boundaries")
            num_sub_seqs = (len(sequence_boundaries) - 1) if sequence_boundaries and len(sequence_boundaries) > 1 else 1
            image_subseq_ids = sample_packing.get("image_subseq_ids") or []
            video_subseq_ids = sample_packing.get("video_subseq_ids") or []
            images_per_subseq = (
                [image_subseq_ids.count(i) for i in range(num_sub_seqs)] if image_subseq_ids and num_sub_seqs > 1 else None
            )
            videos_per_subseq = (
                [video_subseq_ids.count(i) for i in range(num_sub_seqs)] if video_subseq_ids and num_sub_seqs > 1 else None
            )
            if has_dummy_image:
                mm_inputs = {}

            if num_sub_seqs <= 1:
                sample_features = {
                    "input_ids": features["input_ids"],
                    "attention_mask": features["attention_mask"][sample_idx : sample_idx + 1],
                }
                mm_inputs_for_sample = _slice_mm_inputs_for_sample(
                    mm_inputs, batch_imglens, batch_vidlens, sample_idx=sample_idx
                )
                self._compute_rope_position_ids(sample_features, mm_inputs_for_sample)
                all_position_ids.append(sample_features["position_ids"])
                all_rope_deltas.append(sample_features["rope_deltas"])
            else:
                # when we do packing, don't need rope_deltas when training.
                sample_position_ids: list[torch.Tensor] = []
                for subseq_idx in range(num_sub_seqs):
                    subseq_start = sequence_boundaries[subseq_idx]
                    subseq_end = sequence_boundaries[subseq_idx + 1]
                    subseq_features = {
                        "input_ids": features["input_ids"][sample_idx : sample_idx + 1, subseq_start:subseq_end],
                        "attention_mask": features["attention_mask"][sample_idx : sample_idx + 1, subseq_start:subseq_end],
                    }
                    mm_inputs_for_subseq = _slice_mm_inputs_for_sample(
                        mm_inputs,
                        batch_imglens,
                        batch_vidlens,
                        sample_idx,
                        images_per_subseq,
                        videos_per_subseq,
                        subseq_idx
                    )
                    self._compute_rope_position_ids(subseq_features, mm_inputs_for_subseq)
                    sample_position_ids.append(subseq_features["position_ids"])
                all_position_ids.append(torch.cat(sample_position_ids, dim=-1))

        batch_dim_for_position_ids = 1 if all_position_ids[0].dim() == 3 else 0

        features["position_ids"] = torch.cat(all_position_ids, dim=batch_dim_for_position_ids)
        if has_dummy_image:
            mm_inputs = dummy_mm_inputs

        expected_position_ids_shape = (bsz, seq_len) if all_position_ids[0].dim() == 2 else (
            all_position_ids[0].size(0),
            bsz,
            seq_len,
        )
        # Check if position_ids shape matches expected shape.
        # for further usage, we should padding to the right when some padding token on the right.
        if has_dummy_image:
            features["position_ids"] = torch.cat([features["position_ids"], dummy_image_right_padding_mrope], dim=-1)
            features["attention_mask"] = torch.cat([features["attention_mask"], dummy_image_right_padding_attention_mask], dim=-1)

        if features["position_ids"].shape != expected_position_ids_shape:
            raise ValueError(
                "Merged position_ids shape mismatch: "
                f"got {features['position_ids'].shape}, expected {expected_position_ids_shape}."
            )