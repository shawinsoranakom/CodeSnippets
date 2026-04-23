def _assemble_fraction_of_explained_deviance(
    numerator, denominator, n_outputs, multioutput, force_finite, xp, device
):
    """Common part used by explained variance score and :math:`R^2` score."""
    dtype = numerator.dtype

    nonzero_denominator = denominator != 0

    if not force_finite:
        # Standard formula, that may lead to NaN or -Inf
        output_scores = 1 - (numerator / denominator)
    else:
        nonzero_numerator = numerator != 0
        # Default = Zero Numerator = perfect predictions. Set to 1.0
        # (note: even if denominator is zero, thus avoiding NaN scores)
        output_scores = xp.ones([n_outputs], device=device, dtype=dtype)
        # Non-zero Numerator and Non-zero Denominator: use the formula
        valid_score = nonzero_denominator & nonzero_numerator

        output_scores[valid_score] = 1 - (
            numerator[valid_score] / denominator[valid_score]
        )

        # Non-zero Numerator and Zero Denominator:
        # arbitrary set to 0.0 to avoid -inf scores
        output_scores[nonzero_numerator & ~nonzero_denominator] = 0.0

    if isinstance(multioutput, str):
        if multioutput == "raw_values":
            # return scores individually
            return output_scores
        elif multioutput == "uniform_average":
            # pass None as weights to _average: uniform mean
            avg_weights = None
        elif multioutput == "variance_weighted":
            avg_weights = denominator
            if not xp.any(nonzero_denominator):
                # All weights are zero, _average would raise a ZeroDiv error.
                # This only happens when all y are constant (or 1-element long)
                # Since weights are all equal, fall back to uniform weights.
                avg_weights = None
    else:
        avg_weights = multioutput

    result = _average(output_scores, weights=avg_weights, xp=xp)
    if size(result) == 1:
        return float(result)
    return result