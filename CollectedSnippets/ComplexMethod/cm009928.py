def _determine_input_key(
    config: smith_eval.RunEvalConfig,
    run_inputs: list[str] | None,
) -> str | None:
    input_key = None
    if config.input_key:
        input_key = config.input_key
        if run_inputs and input_key not in run_inputs:
            logger.warning(
                "Input key %s not in chain's specified input keys %s. "
                "Evaluation behavior may be undefined.",
                input_key,
                run_inputs,
            )
    elif run_inputs and len(run_inputs) == 1:
        input_key = run_inputs[0]
    elif run_inputs is not None and len(run_inputs) > 1:
        logger.warning(
            "Chain expects multiple input keys: %s,"
            " Evaluator is likely to fail. Evaluation behavior may be undefined."
            " Specify an input_key in the RunEvalConfig to avoid this warning.",
            run_inputs,
        )

    return input_key