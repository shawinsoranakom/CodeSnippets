def prepare(
        cls,
        client: Client,
        dataset_name: str,
        llm_or_chain_factory: MODEL_OR_CHAIN_FACTORY,
        project_name: str | None,
        evaluation: smith_eval.RunEvalConfig | None = None,
        tags: list[str] | None = None,
        input_mapper: Callable[[dict], Any] | None = None,
        concurrency_level: int = 5,
        project_metadata: dict[str, Any] | None = None,
        revision_id: str | None = None,
        dataset_version: datetime | str | None = None,
    ) -> _DatasetRunContainer:
        project_name = project_name or name_generation.random_name()
        if revision_id:
            if not project_metadata:
                project_metadata = {}
            project_metadata.update({"revision_id": revision_id})
        wrapped_model, project, dataset, examples = _prepare_eval_run(
            client,
            dataset_name,
            llm_or_chain_factory,
            project_name,
            project_metadata=project_metadata,
            tags=tags,
            dataset_version=dataset_version,
        )
        tags = tags or []
        for k, v in (project.metadata.get("git") or {}).items():
            tags.append(f"git:{k}={v}")
        run_metadata = {"dataset_version": project.metadata["dataset_version"]}
        if revision_id:
            run_metadata["revision_id"] = revision_id
        wrapped_model = _wrap_in_chain_factory(llm_or_chain_factory)
        run_evaluators = _setup_evaluation(
            wrapped_model,
            examples,
            evaluation,
            dataset.data_type or DataType.kv,
        )
        _validate_example_inputs(examples[0], wrapped_model, input_mapper)
        progress_bar = progress.ProgressBarCallback(len(examples))
        configs = [
            RunnableConfig(
                callbacks=[
                    LangChainTracer(
                        project_name=project.name,
                        client=client,
                        example_id=example.id,
                    ),
                    EvaluatorCallbackHandler(
                        evaluators=run_evaluators or [],
                        client=client,
                        example_id=example.id,
                        max_concurrency=0,
                    ),
                    progress_bar,
                ],
                tags=tags,
                max_concurrency=concurrency_level,
                metadata=run_metadata,
            )
            for example in examples
        ]
        return cls(
            client=client,
            project=project,
            wrapped_model=wrapped_model,
            examples=examples,
            configs=configs,
            batch_evaluators=evaluation.batch_evaluators if evaluation else None,
        )