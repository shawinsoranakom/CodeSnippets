def create_job(payload: RecipePayload, request: Request):
    recipe = payload.recipe
    if not recipe.get("columns"):
        raise HTTPException(status_code = 400, detail = "Recipe must include columns.")

    run: dict[str, Any] = payload.run or {}
    run.pop("artifact_path", None)
    run.pop("dataset_name", None)
    execution_type = str(run.get("execution_type") or "full").strip().lower()
    if execution_type not in {"preview", "full"}:
        raise HTTPException(
            status_code = 400,
            detail = "invalid execution_type: must be 'preview' or 'full'",
        )
    run["execution_type"] = execution_type
    run["run_name"] = _normalize_run_name(run.get("run_name"))
    run_config_raw = run.get("run_config")
    if run_config_raw is not None:
        try:
            from data_designer.config.run_config import RunConfig

            RunConfig.model_validate(run_config_raw)
        except (ImportError, ValidationError, TypeError, ValueError) as exc:
            raise HTTPException(
                status_code = 400, detail = f"invalid run_config: {exc}"
            ) from exc

    try:
        _inject_local_providers(recipe, request)
    except ValueError as exc:
        raise HTTPException(status_code = 400, detail = str(exc)) from exc

    mgr = get_job_manager()
    try:
        job_id = mgr.start(recipe = recipe, run = run)
    except RuntimeError as exc:
        raise HTTPException(status_code = 409, detail = str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code = 400, detail = str(exc)) from exc

    return {"job_id": job_id}