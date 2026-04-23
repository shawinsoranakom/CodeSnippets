def _handle_load(backend, cmd: dict, resp_queue: Any) -> None:
    """Handle a load_checkpoint command."""
    checkpoint_path = cmd["checkpoint_path"]
    max_seq_length = cmd.get("max_seq_length", 2048)
    load_in_4bit = cmd.get("load_in_4bit", True)
    trust_remote_code = cmd.get("trust_remote_code", False)

    # Auto-enable trust_remote_code for NemotronH/Nano models.
    if not trust_remote_code:
        _NEMOTRON_TRUST_SUBSTRINGS = ("nemotron_h", "nemotron-h", "nemotron-3-nano")
        _cp_lower = checkpoint_path.lower()
        if any(sub in _cp_lower for sub in _NEMOTRON_TRUST_SUBSTRINGS) and (
            _cp_lower.startswith("unsloth/") or _cp_lower.startswith("nvidia/")
        ):
            trust_remote_code = True
            logger.info(
                "Auto-enabled trust_remote_code for Nemotron model: %s",
                checkpoint_path,
            )

    try:
        _send_response(
            resp_queue,
            {
                "type": "status",
                "message": f"Loading checkpoint: {checkpoint_path}",
                "ts": time.time(),
            },
        )

        success, message = backend.load_checkpoint(
            checkpoint_path = checkpoint_path,
            max_seq_length = max_seq_length,
            load_in_4bit = load_in_4bit,
            trust_remote_code = trust_remote_code,
        )

        _send_response(
            resp_queue,
            {
                "type": "loaded",
                "success": success,
                "message": message,
                "checkpoint": checkpoint_path if success else None,
                "is_vision": backend.is_vision if success else False,
                "is_peft": backend.is_peft if success else False,
                "ts": time.time(),
            },
        )

    except Exception as exc:
        _send_response(
            resp_queue,
            {
                "type": "loaded",
                "success": False,
                "message": str(exc),
                "stack": traceback.format_exc(limit = 20),
                "ts": time.time(),
            },
        )