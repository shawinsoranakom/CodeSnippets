def on_model_save(trainer):
    """Upload model checkpoint (rate limited to every 15 min)."""
    ctx = getattr(trainer, "platform", None)
    if not ctx or RANK not in {-1, 0} or not trainer.args.project:
        return

    # Rate limit to every 15 minutes (900 seconds)
    if time() - ctx["last_upload"] < 900:
        return

    model_path = trainer.best if trainer.best and Path(trainer.best).exists() else trainer.last
    if not model_path:
        return

    project, name = _get_project_name(trainer)
    _upload_model_async(model_path, project, name, model_id=ctx["model_id"])
    ctx["last_upload"] = time()