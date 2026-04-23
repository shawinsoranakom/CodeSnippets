def _construct_run_evaluator(
    eval_config: smith_eval_config.SINGLE_EVAL_CONFIG_TYPE
    | smith_eval_config.CUSTOM_EVALUATOR_TYPE,
    eval_llm: BaseLanguageModel | None,
    run_type: str,
    data_type: DataType,
    example_outputs: list[str] | None,
    reference_key: str | None,
    input_key: str | None,
    prediction_key: str | None,
) -> RunEvaluator:
    if isinstance(eval_config, RunEvaluator):
        return eval_config
    if isinstance(eval_config, (EvaluatorType, str)):
        if not isinstance(eval_config, EvaluatorType):
            eval_config = EvaluatorType(eval_config)
        evaluator_ = load_evaluator(eval_config, llm=eval_llm)
        eval_type_tag = eval_config.value
    elif isinstance(eval_config, smith_eval_config.EvalConfig):
        kwargs = {"llm": eval_llm, **eval_config.get_kwargs()}
        evaluator_ = load_evaluator(eval_config.evaluator_type, **kwargs)
        eval_type_tag = eval_config.evaluator_type.value
        # Override keys if specified in the config
        if isinstance(eval_config, smith_eval_config.SingleKeyEvalConfig):
            input_key = eval_config.input_key or input_key
            prediction_key = eval_config.prediction_key or prediction_key
            reference_key = eval_config.reference_key or reference_key
    elif callable(eval_config):
        # Assume we can decorate
        return run_evaluator_dec(eval_config)
    else:
        msg = f"Unknown evaluator type: {type(eval_config)}"
        raise ValueError(msg)  # noqa: TRY004

    if isinstance(evaluator_, StringEvaluator):
        if evaluator_.requires_reference and reference_key is None:
            msg = (
                f"Must specify reference_key in smith_eval.RunEvalConfig to use"
                f" evaluator of type {eval_type_tag} with"
                f" dataset with multiple output keys: {example_outputs}."
            )
            raise ValueError(msg)
        run_evaluator = smith_eval.StringRunEvaluatorChain.from_run_and_data_type(
            evaluator_,
            run_type,
            data_type,
            input_key=input_key,
            prediction_key=prediction_key,
            reference_key=reference_key,
            tags=[eval_type_tag],
        )
    elif isinstance(evaluator_, PairwiseStringEvaluator):
        msg = (
            f"Run evaluator for {eval_type_tag} is not implemented."
            " PairwiseStringEvaluators compare the outputs of two different models"
            " rather than the output of a single model."
            " Did you mean to use a StringEvaluator instead?"
            "\nSee: https://python.langchain.com/docs/guides/evaluation/string/"
        )
        raise NotImplementedError(msg)

    else:
        msg = f"Run evaluator for {eval_type_tag} is not implemented"
        raise NotImplementedError(msg)
    return run_evaluator