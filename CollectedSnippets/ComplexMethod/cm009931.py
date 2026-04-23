def _load_run_evaluators(
    config: smith_eval.RunEvalConfig,
    run_type: str,
    data_type: DataType,
    example_outputs: list[str] | None,
    run_inputs: list[str] | None,
    run_outputs: list[str] | None,
) -> list[RunEvaluator]:
    """Load run evaluators from a configuration.

    Args:
        config: Configuration for the run evaluators.
        run_type: The type of run.
        data_type: The type of dataset used in the run.
        example_outputs: The example outputs.
        run_inputs: The input keys for the run.
        run_outputs: The output keys for the run.

    Returns:
        A list of run evaluators.
    """
    run_evaluators = []
    input_key, prediction_key, reference_key = None, None, None
    if config.evaluators or (
        config.custom_evaluators
        and any(isinstance(e, StringEvaluator) for e in config.custom_evaluators)
    ):
        input_key, prediction_key, reference_key = _get_keys(
            config,
            run_inputs,
            run_outputs,
            example_outputs,
        )
    for eval_config in config.evaluators:
        run_evaluator = _construct_run_evaluator(
            eval_config,
            config.eval_llm,
            run_type,
            data_type,
            example_outputs,
            reference_key,
            input_key,
            prediction_key,
        )
        run_evaluators.append(run_evaluator)
    custom_evaluators = config.custom_evaluators or []
    for custom_evaluator in custom_evaluators:
        if isinstance(custom_evaluator, RunEvaluator):
            run_evaluators.append(custom_evaluator)
        elif isinstance(custom_evaluator, StringEvaluator):
            run_evaluators.append(
                smith_eval.StringRunEvaluatorChain.from_run_and_data_type(
                    custom_evaluator,
                    run_type,
                    data_type,
                    input_key=input_key,
                    prediction_key=prediction_key,
                    reference_key=reference_key,
                ),
            )
        elif callable(custom_evaluator):
            run_evaluators.append(run_evaluator_dec(custom_evaluator))
        else:
            msg = (  # type: ignore[unreachable]
                f"Unsupported custom evaluator: {custom_evaluator}."
                f" Expected RunEvaluator or StringEvaluator."
            )
            raise ValueError(msg)  # noqa: TRY004

    return run_evaluators