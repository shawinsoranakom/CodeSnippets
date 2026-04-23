def compute_mm_prefix_range_tensor(
        mm_prefix_range: dict[int, list[tuple[int, int]]] | None,
        num_seqs: int,
        device: torch.device,
    ) -> torch.Tensor | None:
        """Convert mm_prefix_range dict to padded tensor for Triton kernel.

        Returns shape: (num_seqs, max_ranges, 2) with 0-padding for empty ranges.
        Empty ranges have start==end==0, which kernel skips via is_valid check.
        """
        if mm_prefix_range is None:
            return None

        # Collect ranges, using [(0,0)] for empty sequences to ensure uniform dims
        range_lists = [
            mm_prefix_range.get(i, [(0, 0)]) or [(0, 0)] for i in range(num_seqs)
        ]

        # Return None if all ranges are trivial (only (0,0) placeholders)
        if all(r == [(0, 0)] for r in range_lists):
            return None

        # Build on CPU first then move to GPU in a single H2D transfer
        max_ranges = max(len(r) for r in range_lists)
        # Pad all sequences to the same number of ranges
        padded = []
        for r in range_lists:
            padded_r = list(r) + [(0, 0)] * (max_ranges - len(r))
            padded.append(padded_r)
        # Create tensor with efficient H2D transfer
        return torch.tensor(padded, dtype=torch.int32, device=device).view(
            num_seqs, max_ranges, 2
        )