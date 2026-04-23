def publish_job_dataset(job_id: str, payload: PublishDatasetRequest):
    repo_id = payload.repo_id.strip()
    description = payload.description.strip()
    hf_token = payload.hf_token.strip() if isinstance(payload.hf_token, str) else None
    artifact_path = (
        payload.artifact_path.strip()
        if isinstance(payload.artifact_path, str)
        else None
    )

    if not repo_id:
        raise HTTPException(status_code = 400, detail = "repo_id is required")
    if not description:
        raise HTTPException(status_code = 400, detail = "description is required")

    mgr = get_job_manager()
    status = mgr.get_status(job_id)
    if status is not None:
        if (
            status.get("status") != "completed"
            or status.get("execution_type") != "full"
        ):
            raise HTTPException(
                status_code = 409,
                detail = "Only completed full runs can be published.",
            )
        status_artifact = status.get("artifact_path")
        if isinstance(status_artifact, str) and status_artifact.strip():
            artifact_path = status_artifact.strip()

    if not artifact_path:
        raise HTTPException(
            status_code = 400,
            detail = "This execution does not have publishable dataset artifacts.",
        )

    try:
        url = publish_recipe_dataset(
            artifact_path = artifact_path,
            repo_id = repo_id,
            description = description,
            hf_token = hf_token or None,
            private = payload.private,
        )
    except RecipeDatasetPublishError as exc:
        raise HTTPException(status_code = 400, detail = str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code = 500, detail = str(exc)) from exc

    return {
        "success": True,
        "url": url,
        "message": f"Published dataset to {repo_id}.",
    }