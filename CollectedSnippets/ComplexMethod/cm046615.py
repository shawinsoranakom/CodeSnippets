def run_job_process(
    *,
    event_queue,
    recipe: dict[str, Any],
    run: dict[str, Any],
) -> None:
    """
    Subprocess entrypoint.
    Sends events to `event_queue`.
    """
    import os

    os.environ["PYTHONWARNINGS"] = (
        "ignore"  # Suppress warnings at C-level before imports
    )

    import warnings
    from loggers.config import LogConfig

    if os.getenv("ENVIRONMENT_TYPE", "production") == "production":
        warnings.filterwarnings("ignore")

    LogConfig.setup_logging(
        service_name = "unsloth-studio-data-worker",
        env = os.getenv("ENVIRONMENT_TYPE", "production"),
    )

    event_queue.put({"type": EVENT_JOB_STARTED, "ts": time.time()})

    try:
        from data_designer.config.run_config import RunConfig

        rows = int(run.get("rows") or 1000)
        job_id = str(run.get("_job_id") or "").strip()
        if not job_id:
            job_id = f"{int(time.time())}"
        run_name_raw = run.get("run_name")
        run_name = run_name_raw if isinstance(run_name_raw, str) else None
        dataset_name = _build_dataset_name(
            run_name = run_name,
            job_id = job_id,
            artifact_root = _ARTIFACT_ROOT,
        )
        merge_batches = bool(run.get("merge_batches"))
        ensure_dir(_ARTIFACT_ROOT)
        run_config_raw = run.get("run_config") or {}

        builder = build_config_builder(recipe)
        designer = create_data_designer(recipe, artifact_path = str(_ARTIFACT_ROOT))

        # DataDesigner configures root logging in DataDesigner.__init__.
        # Attach queue logger directly to `data_designer` so parser events survive root resets.
        handler = _QueueLogHandler(event_queue)
        handler.setLevel(logging.INFO)
        data_designer_logger = logging.getLogger("data_designer")
        data_designer_logger.addHandler(handler)
        data_designer_logger.setLevel(logging.INFO)
        data_designer_logger.propagate = True

        if run_config_raw:
            designer.set_run_config(RunConfig.model_validate(run_config_raw))

        execution_type = str(run.get("execution_type") or "full").strip().lower()
        if execution_type == "preview":
            results = designer.preview(builder, num_records = rows)
            analysis = (
                None
                if results.analysis is None
                else to_jsonable(results.analysis.model_dump(mode = "json"))
            )
            dataset = (
                []
                if results.dataset is None
                else to_preview_jsonable(results.dataset.to_dict(orient = "records"))
            )
            processor_artifacts = (
                None
                if results.processor_artifacts is None
                else to_jsonable(results.processor_artifacts)
            )
            event_queue.put(
                {
                    "type": EVENT_JOB_COMPLETED,
                    "ts": time.time(),
                    "analysis": analysis,
                    "dataset": dataset,
                    "processor_artifacts": processor_artifacts,
                    "artifact_path": None,
                    "execution_type": execution_type,
                }
            )
        else:
            results = designer.create(
                builder, num_records = rows, dataset_name = dataset_name
            )
            analysis = to_jsonable(results.load_analysis().model_dump(mode = "json"))
            if merge_batches:
                _merge_batches_to_single_parquet(
                    results.artifact_storage.base_dataset_path
                )
            artifact_path = str(results.artifact_storage.base_dataset_path)
            event_queue.put(
                {
                    "type": EVENT_JOB_COMPLETED,
                    "ts": time.time(),
                    "analysis": analysis,
                    "artifact_path": artifact_path,
                    "execution_type": execution_type,
                }
            )
    except Exception as exc:
        event_queue.put(
            {
                "type": EVENT_JOB_ERROR,
                "ts": time.time(),
                "error": str(exc),
                "stack": traceback.format_exc(limit = 20),
            }
        )