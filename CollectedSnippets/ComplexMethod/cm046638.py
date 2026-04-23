def run_inference_process(
    *,
    cmd_queue: Any,
    resp_queue: Any,
    cancel_event,
    config: dict,
) -> None:
    """Subprocess entrypoint. Persistent — runs command loop until shutdown.

    Args:
        cmd_queue: mp.Queue for receiving commands from parent.
        resp_queue: mp.Queue for sending responses to parent.
        cancel_event: mp.Event shared with parent — set by parent to cancel generation.
        config: Initial configuration dict with model info.
    """
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["PYTHONWARNINGS"] = (
        "ignore"  # Suppress warnings at C-level before imports
    )

    if config.get("disable_xet"):
        os.environ["HF_HUB_DISABLE_XET"] = "1"
        logger.info("Xet transport disabled (HF_HUB_DISABLE_XET=1)")

    import warnings
    from loggers.config import LogConfig

    if os.getenv("ENVIRONMENT_TYPE", "production") == "production":
        warnings.filterwarnings("ignore")

    LogConfig.setup_logging(
        service_name = "unsloth-studio-inference-worker",
        env = os.getenv("ENVIRONMENT_TYPE", "production"),
    )

    apply_gpu_ids(config.get("resolved_gpu_ids"))

    model_name = config["model_name"]

    # ── 1. Activate correct transformers version BEFORE any ML imports ──
    try:
        _activate_transformers_version(model_name)
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

        from core.inference.inference import InferenceBackend

        import transformers

        logger.info("Subprocess loaded transformers %s", transformers.__version__)

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

    # ── 3. Create inference backend and load initial model ──
    try:
        backend = InferenceBackend()

        _send_response(
            resp_queue,
            {
                "type": "status",
                "message": "Loading model...",
                "ts": time.time(),
            },
        )

        _handle_load(backend, config, resp_queue)

    except Exception as exc:
        _send_response(
            resp_queue,
            {
                "type": "error",
                "error": f"Failed to initialize inference backend: {exc}",
                "stack": traceback.format_exc(limit = 20),
                "ts": time.time(),
            },
        )
        return

    # ── 4. Command loop — process commands until shutdown ──
    # cancel_event is an mp.Event shared with parent — parent can set it
    # at any time to cancel generation instantly (no queue polling needed).
    logger.info("Inference subprocess ready, entering command loop")

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
            if cmd_type == "generate":
                cancel_event.clear()
                _handle_generate(backend, cmd, resp_queue, cancel_event)

            elif cmd_type == "load":
                # Load a new model (reusing this subprocess)
                # First unload current model
                if backend.active_model_name:
                    backend.unload_model(backend.active_model_name)
                _handle_load(backend, cmd, resp_queue)

            elif cmd_type == "generate_audio":
                cancel_event.clear()
                _handle_generate_audio(backend, cmd, resp_queue)

            elif cmd_type == "generate_audio_input":
                cancel_event.clear()
                _handle_generate_audio_input(backend, cmd, resp_queue, cancel_event)

            elif cmd_type == "unload":
                _handle_unload(backend, cmd, resp_queue)

            elif cmd_type == "cancel":
                # Redundant with mp.Event but handle gracefully
                cancel_event.set()
                logger.info("Cancel command received")

            elif cmd_type == "reset":
                cancel_event.set()
                backend.reset_generation_state()
                _send_response(
                    resp_queue,
                    {
                        "type": "reset_ack",
                        "ts": time.time(),
                    },
                )

            elif cmd_type == "status":
                # Return current status
                _send_response(
                    resp_queue,
                    {
                        "type": "status_response",
                        "active_model": backend.active_model_name,
                        "models": {
                            name: {
                                "is_vision": info.get("is_vision", False),
                                "is_lora": info.get("is_lora", False),
                            }
                            for name, info in backend.models.items()
                        },
                        "loading": list(backend.loading_models),
                        "ts": time.time(),
                    },
                )

            elif cmd_type == "shutdown":
                logger.info("Shutdown command received, exiting")
                # Unload all models
                for model_name in list(backend.models.keys()):
                    try:
                        backend.unload_model(model_name)
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