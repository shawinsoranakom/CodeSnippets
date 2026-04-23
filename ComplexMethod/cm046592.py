def run_export_process(
    *,
    cmd_queue: Any,
    resp_queue: Any,
    config: dict,
) -> None:
    """Subprocess entrypoint. Persistent — runs command loop until shutdown.

    Args:
        cmd_queue: mp.Queue for receiving commands from parent.
        resp_queue: mp.Queue for sending responses to parent.
        config: Initial configuration dict with checkpoint_path.
    """
    import queue as _queue

    # Install fd-level stdout/stderr capture FIRST so every subsequent
    # print and every child process inherits the redirected fds. This
    # is what powers the live export log stream in the UI.
    _setup_log_capture(resp_queue)

    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["PYTHONWARNINGS"] = (
        "ignore"  # Suppress warnings at C-level before imports
    )
    # Force unbuffered output from any child Python process (e.g. the
    # GGUF converter) so their prints surface in the log stream as they
    # happen rather than at the end.
    os.environ["PYTHONUNBUFFERED"] = "1"
    # tqdm defaults to a 10-second mininterval when stdout is not a tty
    # (which it isn't here -- we redirected fd 1/2 to a pipe). That makes
    # multi-step progress bars look frozen in the export log panel. Force
    # frequent flushes so the user sees movement during merge / GGUF
    # conversion. Has no effect on single-step bars (e.g. "Copying 1
    # files") which only emit start/end events regardless.
    os.environ.setdefault("TQDM_MININTERVAL", "0.5")

    import warnings
    from loggers.config import LogConfig

    if os.getenv("ENVIRONMENT_TYPE", "production") == "production":
        warnings.filterwarnings("ignore")

    LogConfig.setup_logging(
        service_name = "unsloth-studio-export-worker",
        env = os.getenv("ENVIRONMENT_TYPE", "production"),
    )

    checkpoint_path = config["checkpoint_path"]

    # ── 1. Activate correct transformers version BEFORE any ML imports ──
    try:
        _activate_transformers_version(checkpoint_path)
    except Exception as exc:
        _send_response(
            resp_queue,
            {
                "type": "error",
                "error": f"Failed to activate transformers version: {exc}",
                "stack": traceback.format_exc(limit = 20),
                "ts": time.time(),
            },
        )
        return

    # ── 1b. On Windows, check Triton availability (must be before import torch) ──
    if sys.platform == "win32":
        try:
            import triton  # noqa: F401

            logger.info("Triton available — torch.compile enabled")
        except ImportError:
            os.environ["TORCHDYNAMO_DISABLE"] = "1"
            logger.warning(
                "Triton not found on Windows — torch.compile disabled. "
                'Install for better performance: pip install "triton-windows<3.7"'
            )

    # ── 2. Import ML libraries (fresh in this clean process) ──
    try:
        _send_response(
            resp_queue,
            {
                "type": "status",
                "message": "Importing Unsloth...",
                "ts": time.time(),
            },
        )

        backend_path = str(Path(__file__).resolve().parent.parent.parent)
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)

        from core.export.export import ExportBackend

        import transformers

        logger.info(
            "Export subprocess loaded transformers %s", transformers.__version__
        )

    except Exception as exc:
        _send_response(
            resp_queue,
            {
                "type": "error",
                "error": f"Failed to import ML libraries: {exc}",
                "stack": traceback.format_exc(limit = 20),
                "ts": time.time(),
            },
        )
        return

    # ── 3. Create export backend and load initial checkpoint ──
    try:
        backend = ExportBackend()

        _handle_load(backend, config, resp_queue)

    except Exception as exc:
        _send_response(
            resp_queue,
            {
                "type": "error",
                "error": f"Failed to initialize export backend: {exc}",
                "stack": traceback.format_exc(limit = 20),
                "ts": time.time(),
            },
        )
        return

    # ── 4. Command loop — process commands until shutdown ──
    logger.info("Export subprocess ready, entering command loop")

    while True:
        try:
            cmd = cmd_queue.get(timeout = 1.0)
        except _queue.Empty:
            continue
        except (EOFError, OSError):
            logger.info("Command queue closed, shutting down")
            return

        if cmd is None:
            continue

        cmd_type = cmd.get("type", "")
        logger.info("Received command: %s", cmd_type)

        try:
            if cmd_type == "load":
                # Load a new checkpoint (reusing this subprocess)
                backend.cleanup_memory()
                _handle_load(backend, cmd, resp_queue)

            elif cmd_type == "export":
                _handle_export(backend, cmd, resp_queue)

            elif cmd_type == "cleanup":
                _handle_cleanup(backend, resp_queue)

            elif cmd_type == "status":
                _send_response(
                    resp_queue,
                    {
                        "type": "status_response",
                        "checkpoint": backend.current_checkpoint,
                        "is_vision": backend.is_vision,
                        "is_peft": backend.is_peft,
                        "ts": time.time(),
                    },
                )

            elif cmd_type == "shutdown":
                logger.info("Shutdown command received, cleaning up and exiting")
                try:
                    backend.cleanup_memory()
                except Exception:
                    pass
                _send_response(
                    resp_queue,
                    {
                        "type": "shutdown_ack",
                        "ts": time.time(),
                    },
                )
                return

            else:
                logger.warning("Unknown command type: %s", cmd_type)
                _send_response(
                    resp_queue,
                    {
                        "type": "error",
                        "error": f"Unknown command type: {cmd_type}",
                        "ts": time.time(),
                    },
                )

        except Exception as exc:
            logger.error(
                "Error handling command '%s': %s", cmd_type, exc, exc_info = True
            )
            _send_response(
                resp_queue,
                {
                    "type": "error",
                    "error": f"Command '{cmd_type}' failed: {exc}",
                    "stack": traceback.format_exc(limit = 20),
                    "ts": time.time(),
                },
            )