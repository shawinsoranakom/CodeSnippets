def _prepare_eval_run(
    client: Client,
    dataset_name: str,
    llm_or_chain_factory: MODEL_OR_CHAIN_FACTORY,
    project_name: str,
    project_metadata: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    dataset_version: str | datetime | None = None,
) -> tuple[MCF, TracerSession, Dataset, list[Example]]:
    wrapped_model = _wrap_in_chain_factory(llm_or_chain_factory, dataset_name)
    dataset = client.read_dataset(dataset_name=dataset_name)

    examples = list(client.list_examples(dataset_id=dataset.id, as_of=dataset_version))
    if not examples:
        msg = f"Dataset {dataset_name} has no example rows."
        raise ValueError(msg)
    modified_at = [ex.modified_at for ex in examples if ex.modified_at]
    # Should always be defined in practice when fetched,
    # but the typing permits None
    max_modified_at = max(modified_at) if modified_at else None
    inferred_version = max_modified_at.isoformat() if max_modified_at else None

    try:
        project_metadata = project_metadata or {}
        git_info = get_git_info()
        if git_info:
            project_metadata = {
                **project_metadata,
                "git": git_info,
            }

        project_metadata["dataset_version"] = inferred_version
        project = client.create_project(
            project_name,
            reference_dataset_id=dataset.id,
            project_extra={"tags": tags} if tags else {},
            metadata=project_metadata,
        )
    except (HTTPError, ValueError, LangSmithError) as e:
        if "already exists " not in str(e):
            raise
        uid = uuid.uuid4()
        example_msg = f"""
run_on_dataset(
    ...
    project_name="{project_name} - {uid}", # Update since {project_name} already exists
)
"""
        msg = (
            f"Test project {project_name} already exists. Please use a different name:"
            f"\n\n{example_msg}"
        )
        raise ValueError(msg) from e
    comparison_url = dataset.url + f"/compare?selectedSessions={project.id}"
    print(  # noqa: T201
        f"View the evaluation results for project '{project_name}'"
        f" at:\n{comparison_url}\n\n"
        f"View all tests for Dataset {dataset_name} at:\n{dataset.url}",
        flush=True,
    )
    return wrapped_model, project, dataset, examples