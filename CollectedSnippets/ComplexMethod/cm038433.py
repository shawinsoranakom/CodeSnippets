def preserve_intragpu_slots(
        cls,
        phy2log: np.ndarray,
        num_ranks: int,
        old_phy2log: np.ndarray,
    ) -> np.ndarray:
        """
        Reorder the new mapping per GPU so that experts that remain on the same GPU
        keep their previous slot positions when possible. Incoming experts to that GPU
        fill any remaining available slots. This is applied only when the number of GPUs
        is unchanged and the slots per GPU remain the same between
        the old and new mappings.
        """
        num_phy_experts = phy2log.shape[1]
        if num_ranks <= 0 or num_phy_experts % num_ranks != 0:
            return phy2log

        # Move to CPU and convert to NumPy for processing
        slots_per_gpu = num_phy_experts // num_ranks
        num_layers = phy2log.shape[0]

        post_phy2log = phy2log.copy()

        for gpu_idx in range(num_ranks):
            start = gpu_idx * slots_per_gpu
            end = start + slots_per_gpu
            # Experts across all layers for this GPU
            old_local = old_phy2log[:, start:end]  # [layers, slots]
            new_local = phy2log[:, start:end]  # [layers, slots]

            used_new_indices = np.zeros((num_layers, slots_per_gpu), dtype=bool)
            preserved_positions = np.zeros((num_layers, slots_per_gpu), dtype=bool)

            # First pass: preserve same-logical experts in their previous slots
            for slot_idx in range(slots_per_gpu):
                # matches: [layers, slots], True where new local experts have
                # the same logical value as the old from 'slot_idx' and not checked yet
                matches = (new_local == old_local[:, slot_idx][:, None]) & (
                    ~used_new_indices
                )
                has_any = matches.any(axis=1)
                if np.any(has_any):
                    first_idx = np.argmax(matches, axis=1)
                    layer_indices = np.nonzero(has_any)[0]
                    matched_new_positions = first_idx[layer_indices]
                    post_phy2log[layer_indices, start + slot_idx] = new_local[
                        layer_indices, matched_new_positions
                    ]
                    used_new_indices[layer_indices, matched_new_positions] = True
                    preserved_positions[layer_indices, slot_idx] = True

            # Second pass: fill remaining slots with remaining new experts
            remaining_mask = ~used_new_indices  # [layers, slots]
            fill_mask = ~preserved_positions  # [layers, slots]
            if remaining_mask.any() and fill_mask.any():
                idx_base = np.tile(np.arange(slots_per_gpu), (num_layers, 1))
                # Sentinel value for unavailable positions.
                large = slots_per_gpu + 1
                # Priorities: keep original index for available spots, set sentinel
                # for unavailable; lower is earlier.
                remaining_priority = np.where(remaining_mask, idx_base, large)
                fill_priority = np.where(fill_mask, idx_base, large)
                # Sort to get ordered indices of available src/dst positions per layer.
                remaining_indices = np.argsort(remaining_priority, axis=1)
                fill_indices = np.argsort(fill_priority, axis=1)
                # Fill count per layer (cannot exceed either side).
                remaining_counts = remaining_mask.sum(axis=1)
                fill_counts = fill_mask.sum(axis=1)
                take_counts = np.minimum(remaining_counts, fill_counts)
                # Assign remaining new experts to remaining slots per layer.
                for layer_idx in range(num_layers):
                    k = int(take_counts[layer_idx])
                    if k <= 0:
                        continue
                    src_pos = remaining_indices[layer_idx, :k]
                    dst_pos = fill_indices[layer_idx, :k]
                    post_phy2log[layer_idx, start + dst_pos] = new_local[
                        layer_idx, src_pos
                    ]

        return post_phy2log