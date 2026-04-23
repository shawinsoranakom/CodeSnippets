def _graceful_shutdown(server = None):
    """Explicitly shut down all subprocess backends and the uvicorn server.

    Called from signal handlers to ensure child processes are cleaned up
    before the parent exits. This is critical on Windows where atexit
    handlers are unreliable after Ctrl+C.
    """
    _remove_pid_file()
    logger.info("Graceful shutdown initiated — cleaning up subprocesses...")

    # 1. Shut down uvicorn server (releases the listening socket)
    if server is not None:
        server.should_exit = True

    # 2. Clean up inference subprocess (if instantiated)
    try:
        from core.inference.orchestrator import _inference_backend

        if _inference_backend is not None:
            _inference_backend._shutdown_subprocess(timeout = 5.0)
    except Exception as e:
        logger.warning("Error shutting down inference subprocess: %s", e)

    # 3. Clean up export subprocess (if instantiated)
    try:
        from core.export.orchestrator import _export_backend

        if _export_backend is not None:
            _export_backend._shutdown_subprocess(timeout = 5.0)
    except Exception as e:
        logger.warning("Error shutting down export subprocess: %s", e)

    # 4. Clean up training subprocess (if active)
    try:
        from core.training.training import _training_backend

        if _training_backend is not None:
            _training_backend.force_terminate()
    except Exception as e:
        logger.warning("Error shutting down training subprocess: %s", e)

    # 5. Kill llama-server subprocess (if loaded)
    try:
        from routes.inference import _llama_cpp_backend

        if _llama_cpp_backend is not None:
            _llama_cpp_backend._kill_process()
    except Exception as e:
        logger.warning("Error shutting down llama-server: %s", e)

    logger.info("All subprocesses cleaned up")