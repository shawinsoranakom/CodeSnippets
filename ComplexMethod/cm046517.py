async def load_checkpoint(
    request: LoadCheckpointRequest,
    current_subject: str = Depends(get_current_subject),
):
    """
    Load a checkpoint into the export backend.

    Wraps ExportBackend.load_checkpoint.
    """
    try:
        # Version switching is handled automatically by the subprocess-based
        # export backend — no need for ensure_transformers_version() here.

        # Free GPU memory: shut down any running inference/training subprocesses
        # before loading the export checkpoint (they'd compete for VRAM).
        try:
            from core.inference import get_inference_backend

            inf = get_inference_backend()
            if inf.active_model_name:
                logger.info(
                    "Unloading inference model '%s' to free GPU memory for export",
                    inf.active_model_name,
                )
                inf._shutdown_subprocess()
                inf.active_model_name = None
                inf.models.clear()
        except Exception as e:
            logger.warning("Could not unload inference model: %s", e)

        try:
            from core.training import get_training_backend

            trn = get_training_backend()
            if trn.is_training_active():
                logger.info("Stopping active training to free GPU memory for export")
                trn.stop_training()
                # Wait for training subprocess to actually exit before proceeding,
                # otherwise it may still hold GPU memory when export tries to load.
                for _ in range(60):  # up to 30s
                    if not trn.is_training_active():
                        break
                    import time

                    time.sleep(0.5)
                else:
                    logger.warning(
                        "Training subprocess did not exit within 30s, proceeding anyway"
                    )
        except Exception as e:
            logger.warning("Could not stop training: %s", e)

        backend = get_export_backend()
        # load_checkpoint spawns and waits on a subprocess and can take
        # minutes. Run it in a worker thread so the event loop stays
        # free to serve the live log SSE stream concurrently.
        success, message = await asyncio.to_thread(
            backend.load_checkpoint,
            checkpoint_path = request.checkpoint_path,
            max_seq_length = request.max_seq_length,
            load_in_4bit = request.load_in_4bit,
            trust_remote_code = request.trust_remote_code,
        )

        if not success:
            raise HTTPException(status_code = 400, detail = message)

        return ExportOperationResponse(success = True, message = message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading checkpoint: {e}", exc_info = True)
        raise HTTPException(
            status_code = 500,
            detail = f"Failed to load checkpoint: {str(e)}",
        )