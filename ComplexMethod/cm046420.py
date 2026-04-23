def on_train_end(trainer):
    """Log final results, upload best model, and send validation plot data."""
    ctx = getattr(trainer, "platform", None)
    if not ctx or RANK not in {-1, 0} or not trainer.args.project:
        return

    project, name = _get_project_name(trainer)

    if ctx["cancelled"]:
        LOGGER.info(f"{PREFIX}Uploading partial results for cancelled training")

    # Stop console capture
    if ctx["console_logger"]:
        ctx["console_logger"].stop_capture()
        ctx["console_logger"] = None

    # Upload best model (blocking with progress bar to ensure it completes)
    gcs_path = None
    model_size = None
    if trainer.best and Path(trainer.best).exists():
        model_size = Path(trainer.best).stat().st_size
        gcs_path = _upload_model(trainer.best, project, name, progress=True, retry=3, model_id=ctx["model_id"])
        if not gcs_path:
            LOGGER.warning(f"{PREFIX}Model will not be available for download on Platform (upload failed)")

    # Collect plots from trainer and validator, deduplicating by type
    plots_by_type = {}
    for info in getattr(trainer, "plots", {}).values():
        if info.get("data") and info["data"].get("type"):
            plots_by_type[info["data"]["type"]] = info["data"]
    for info in getattr(getattr(trainer, "validator", None), "plots", {}).values():
        if info.get("data") and info["data"].get("type"):
            plots_by_type.setdefault(info["data"]["type"], info["data"])  # Don't overwrite trainer plots
    plots = [_interp_plot(p) for p in plots_by_type.values()]  # Interpolate curves to reduce size

    # Get class names
    names = getattr(getattr(trainer, "validator", None), "names", None) or (trainer.data or {}).get("names")
    class_names = list(names.values()) if isinstance(names, dict) else list(names) if names else None

    _send(
        "training_complete",
        {
            "results": {
                "metrics": {**trainer.metrics, "fitness": trainer.fitness},
                "bestEpoch": getattr(trainer, "best_epoch", trainer.epoch),
                "bestFitness": trainer.best_fitness,
                "modelPath": gcs_path,  # Only send GCS path, not local path
                "modelSize": model_size,
            },
            "classNames": class_names,
            "plots": plots,
        },
        project,
        name,
        ctx["model_id"],
        retry=4,  # Critical, more retries
    )
    url = f"{PLATFORM_URL}/{project}/{ctx.get('model_slug', name)}"
    LOGGER.info(f"{PREFIX}View results at {url}")