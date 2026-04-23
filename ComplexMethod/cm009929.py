def _determine_prediction_key(
    config: smith_eval.RunEvalConfig,
    run_outputs: list[str] | None,
) -> str | None:
    prediction_key = None
    if config.prediction_key:
        prediction_key = config.prediction_key
        if run_outputs and prediction_key not in run_outputs:
            logger.warning(
                "Prediction key %s not in chain's specified output keys %s. "
                "Evaluation behavior may be undefined.",
                prediction_key,
                run_outputs,
            )
    elif run_outputs and len(run_outputs) == 1:
        prediction_key = run_outputs[0]
    elif run_outputs is not None and len(run_outputs) > 1:
        logger.warning(
            "Chain expects multiple output keys: %s,"
            " Evaluation behavior may be undefined. Specify a prediction_key"
            " in the RunEvalConfig to avoid this warning.",
            run_outputs,
        )
    return prediction_key