def _finalize_outputs(
        out,
        lse,
        max_scores,
        *,
        return_aux: AuxRequest | None,
        return_lse: bool,
    ):
        """Normalize stats and build return value (aux-aware, legacy-compatible)."""
        ln2 = math.log(2.0)
        return_lse = return_lse or return_aux is not None and return_aux.lse
        return_max = return_aux is not None and return_aux.max_scores

        lse_scaled = lse * ln2 if (return_lse and lse.numel() > 0) else None
        max_scaled = (
            max_scores * ln2 if (return_max and max_scores.numel() > 0) else None
        )

        if return_aux is not None:
            return out, AuxOutput(
                lse=lse_scaled,
                max_scores=max_scaled,
            )

        if return_lse:
            return out, lse_scaled

        return out