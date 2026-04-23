def on_fit_epoch_end(trainer):
    """Log training and system metrics at epoch end."""
    ctx = getattr(trainer, "platform", None)
    if not ctx or RANK not in {-1, 0} or not trainer.args.project:
        return

    project, name = _get_project_name(trainer)
    metrics = {**trainer.label_loss_items(trainer.tloss, prefix="train"), **trainer.metrics}

    if trainer.optimizer and trainer.optimizer.param_groups:
        metrics["lr"] = trainer.optimizer.param_groups[0]["lr"]

    # Extract model info at epoch 0 (sent as separate field, not in metrics)
    model_info = None
    if trainer.epoch == 0:
        try:
            info = model_info_for_loggers(trainer)
            model_info = {
                "parameters": info.get("model/parameters", 0),
                "gflops": info.get("model/GFLOPs", 0),
                "speedMs": info.get("model/speed_PyTorch(ms)", 0),
            }
        except Exception:
            pass

    # Get system metrics (cache SystemLogger in platform context for efficiency)
    system = {}
    try:
        if not ctx["system_logger"]:
            ctx["system_logger"] = SystemLogger()
        system = ctx["system_logger"].get_metrics(rates=True)
    except Exception:
        pass

    payload = {
        "epoch": trainer.epoch,
        "metrics": metrics,
        "system": system,
        "fitness": trainer.fitness,
        "best_fitness": trainer.best_fitness,
    }
    if model_info:
        payload["modelInfo"] = model_info

    def _send_and_check_cancel():
        """Send epoch_end and check response for cancellation (runs in background thread)."""
        response = _send("epoch_end", payload, project, name, ctx["model_id"], retry=1)
        _handle_control_response(trainer, ctx, response)

    _executor.submit(_send_and_check_cancel)