def run_on_dataset(
    client: Client | None,
    dataset_name: str,
    llm_or_chain_factory: MODEL_OR_CHAIN_FACTORY,
    *,
    evaluation: smith_eval.RunEvalConfig | None = None,
    dataset_version: datetime | str | None = None,
    concurrency_level: int = 5,
    project_name: str | None = None,
    project_metadata: dict[str, Any] | None = None,
    verbose: bool = False,
    revision_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run on dataset.

    Run the Chain or language model on a dataset and store traces
    to the specified project name.

    For the (usually faster) async version of this function,
    see `arun_on_dataset`.

    Args:
        dataset_name: Name of the dataset to run the chain on.
        llm_or_chain_factory: Language model or Chain constructor to run
            over the dataset. The Chain constructor is used to permit
            independent calls on each example without carrying over state.
        evaluation: Configuration for evaluators to run on the
            results of the chain.
        dataset_version: Optional version of the dataset.
        concurrency_level: The number of async tasks to run concurrently.
        project_name: Name of the project to store the traces in.
            Defaults to `{dataset_name}-{chain class name}-{datetime}`.
        project_metadata: Optional metadata to add to the project.
            Useful for storing information the test variant.
            (prompt version, model version, etc.)
        client: LangSmith client to use to access the dataset and to
            log feedback and run traces.
        verbose: Whether to print progress.
        revision_id: Optional revision identifier to assign this test run to
            track the performance of different versions of your system.
        **kwargs: Should not be used, but is provided for backwards compatibility.

    Returns:
        `dict` containing the run's project name and the resulting model outputs.

    Examples:
    ```python
    from langsmith import Client
    from langchain_openai import ChatOpenAI
    from langchain_classic.chains import LLMChain
    from langchain_classic.smith import smith_eval.RunEvalConfig, run_on_dataset

    # Chains may have memory. Passing in a constructor function lets the
    # evaluation framework avoid cross-contamination between runs.
    def construct_chain():
        model = ChatOpenAI(temperature=0)
        chain = LLMChain.from_string(
            model,
            "What's the answer to {your_input_key}"
        )
        return chain

    # Load off-the-shelf evaluators via config or the EvaluatorType (string or enum)
    evaluation_config = smith_eval.RunEvalConfig(
        evaluators=[
            "qa",  # "Correctness" against a reference answer
            "embedding_distance",
            smith_eval.RunEvalConfig.Criteria("helpfulness"),
            smith_eval.RunEvalConfig.Criteria({
                "fifth-grader-score": "Do you have to be smarter than a fifth "
                "grader to answer this question?"
            }),
        ]
    )

    client = Client()
    run_on_dataset(
        client,
        dataset_name="<my_dataset_name>",
        llm_or_chain_factory=construct_chain,
        evaluation=evaluation_config,
    )
    ```

    You can also create custom evaluators by subclassing the `StringEvaluator` or
    LangSmith's `RunEvaluator` classes.

    ```python
    from typing import Optional
    from langchain_classic.evaluation import StringEvaluator


    class MyStringEvaluator(StringEvaluator):
        @property
        def requires_input(self) -> bool:
            return False

        @property
        def requires_reference(self) -> bool:
            return True

        @property
        def evaluation_name(self) -> str:
            return "exact_match"

        def _evaluate_strings(
            self, prediction, reference=None, input=None, **kwargs
        ) -> dict:
            return {"score": prediction == reference}


    evaluation_config = smith_eval.RunEvalConfig(
        custom_evaluators=[MyStringEvaluator()],
    )

    run_on_dataset(
        client,
        dataset_name="<my_dataset_name>",
        llm_or_chain_factory=construct_chain,
        evaluation=evaluation_config,
    )
    ```
    """
    input_mapper = kwargs.pop("input_mapper", None)
    if input_mapper:
        warn_deprecated("0.0.305", message=_INPUT_MAPPER_DEP_WARNING, pending=True)
    tags = kwargs.pop("tags", None)
    if tags:
        warn_deprecated(
            "0.1.9",
            message="The tags argument is deprecated and will be"
            " removed in a future release. Please specify project_metadata instead.",
            pending=True,
        )
    if revision_id is None:
        revision_id = get_langchain_env_var_metadata().get("revision_id")

    if kwargs:
        warn_deprecated(
            "0.0.305",
            message="The following arguments are deprecated and "
            "will be removed in a future release: "
            f"{kwargs.keys()}.",
            removal="0.0.305",
        )
    client = client or Client()
    container = _DatasetRunContainer.prepare(
        client,
        dataset_name,
        llm_or_chain_factory,
        project_name,
        evaluation,
        tags,
        input_mapper,
        concurrency_level,
        project_metadata=project_metadata,
        revision_id=revision_id,
        dataset_version=dataset_version,
    )
    if concurrency_level == 0:
        batch_results = [
            _run_llm_or_chain(
                example,
                config,
                llm_or_chain_factory=container.wrapped_model,
                input_mapper=input_mapper,
            )
            for example, config in zip(
                container.examples, container.configs, strict=False
            )
        ]
    else:
        with runnable_config.get_executor_for_config(container.configs[0]) as executor:
            batch_results = list(
                executor.map(
                    functools.partial(
                        _run_llm_or_chain,
                        llm_or_chain_factory=container.wrapped_model,
                        input_mapper=input_mapper,
                    ),
                    container.examples,
                    container.configs,
                ),
            )

    return container.finish(batch_results, verbose=verbose)