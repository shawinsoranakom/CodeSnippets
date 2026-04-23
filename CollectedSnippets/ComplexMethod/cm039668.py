def _score(estimator, X_test, y_test, scorer, score_params, error_score="raise"):
    """Compute the score(s) of an estimator on a given test set.

    Will return a dict of floats if `scorer` is a _MultiMetricScorer, otherwise a single
    float is returned.
    """
    score_params = {} if score_params is None else score_params

    try:
        if y_test is None:
            scores = scorer(estimator, X_test, **score_params)
        else:
            scores = scorer(estimator, X_test, y_test, **score_params)
    except Exception:
        if isinstance(scorer, _MultimetricScorer):
            # If `_MultimetricScorer` raises exception, the `error_score`
            # parameter is equal to "raise".
            raise
        else:
            if error_score == "raise":
                raise
            else:
                scores = error_score
                warnings.warn(
                    (
                        "Scoring failed. The score on this train-test partition for "
                        f"these parameters will be set to {error_score}. Details: \n"
                        f"{format_exc()}"
                    ),
                    UserWarning,
                )

    # Check non-raised error messages in `_MultimetricScorer`
    if isinstance(scorer, _MultimetricScorer):
        exception_messages = [
            (name, str_e) for name, str_e in scores.items() if isinstance(str_e, str)
        ]
        if exception_messages:
            # error_score != "raise"
            for name, str_e in exception_messages:
                scores[name] = error_score
                warnings.warn(
                    (
                        "Scoring failed. The score on this train-test partition for "
                        f"these parameters will be set to {error_score}. Details: \n"
                        f"{str_e}"
                    ),
                    UserWarning,
                )

    error_msg = "scoring must return a number, got %s (%s) instead. (scorer=%s)"
    if isinstance(scores, dict):
        for name, score in scores.items():
            if hasattr(score, "item"):
                with suppress(ValueError):
                    # e.g. unwrap memmapped scalars
                    score = score.item()
            if not isinstance(score, numbers.Number):
                raise ValueError(error_msg % (score, type(score), name))
            scores[name] = score
    else:  # scalar
        if hasattr(scores, "item"):
            with suppress(ValueError):
                # e.g. unwrap memmapped scalars
                scores = scores.item()
        if not isinstance(scores, numbers.Number):
            raise ValueError(error_msg % (scores, type(scores), scorer))
    return scores