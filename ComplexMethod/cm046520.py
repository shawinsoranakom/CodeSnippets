async def get_training_status(
    current_subject: str = Depends(get_current_subject),
):
    """
    Get the current training status.
    """
    try:
        backend = get_training_backend()
        job_id: str = getattr(backend, "current_job_id", "") or ""

        # Check if training is active
        is_active = backend.is_training_active()

        # Get progress info from trainer
        try:
            progress = backend.trainer.get_training_progress()
        except Exception:
            progress = None

        status_message = (
            getattr(progress, "status_message", None) if progress else None
        ) or "Ready to train"
        error_message = getattr(progress, "error", None) if progress else None

        # Check if training was stopped by user
        trainer_stopped = getattr(backend, "_should_stop", False)

        # Derive high-level phase
        if error_message:
            phase = "error"
        elif is_active:
            msg_lower = status_message.lower()
            if "loading" in msg_lower or "importing" in msg_lower:
                phase = "loading_model"
            elif any(
                k in msg_lower for k in ["preparing", "initializing", "configuring"]
            ):
                phase = "configuring"
            else:
                phase = "training"
        elif trainer_stopped:
            phase = "stopped"
        elif progress and getattr(progress, "is_completed", False):
            phase = "completed"
        else:
            phase = "idle"

        details = None
        if progress:
            details = {
                "epoch": getattr(progress, "epoch", 0),
                "step": getattr(progress, "step", 0),
                "total_steps": getattr(progress, "total_steps", 0),
                "loss": getattr(progress, "loss", None),
                "learning_rate": getattr(progress, "learning_rate", None),
            }

        # Build metric history for chart recovery after SSE reconnection
        metric_history = None
        if backend.step_history:
            metric_history = {
                "steps": list(backend.step_history),
                "loss": list(backend.loss_history),
                "lr": list(backend.lr_history),
                "grad_norm": list(getattr(backend, "grad_norm_history", [])),
                "grad_norm_steps": list(getattr(backend, "grad_norm_step_history", [])),
                "eval_loss": list(backend.eval_loss_history),
                "eval_steps": list(backend.eval_step_history),
            }

        return TrainingStatus(
            job_id = job_id,
            phase = phase,
            is_training_running = is_active,
            eval_enabled = backend.eval_enabled,
            message = status_message,
            error = error_message,
            details = details,
            metric_history = metric_history,
        )

    except Exception as e:
        logger.error(f"Error getting training status: {e}", exc_info = True)
        raise HTTPException(
            status_code = 500, detail = f"Failed to get training status: {str(e)}"
        )