def get_mrope_interleaved_id_list(
        a: int, b: int, c: int, force_last: bool = False
    ) -> list[int]:
        """
        Generate an interleaved list of indices for multi-modal rotary embedding.

        Args:
            a: Number of indices for first modality
            b: Number of indices for second modality
            c: Number of indices for third modality
            force_last: Whether to force the last element to be from the first modality

        Returns:
            List of interleaved indices
        """
        if force_last:
            a -= 1

        counts = {0: a, 1: b, 2: c}
        placed = {k: 0 for k in counts}
        rem = counts.copy()
        seq: list[int] = []
        last = None

        total = a + b + c
        for _ in range(total):
            # Candidates: remaining > 0 and ≠ last
            cands = [k for k in rem if rem[k] > 0 and k != last]
            if not cands:
                # If only last remains, relax the condition
                cands = [k for k in rem if rem[k] > 0]

            # Select the rarest candidate
            try:
                best = min(cands, key=lambda k: (placed[k] / counts[k], k))
            except KeyError:
                best = 0

            seq.append(best)
            placed[best] += 1
            rem[best] -= 1
            last = best

        if force_last:
            seq.append(0)

        return seq