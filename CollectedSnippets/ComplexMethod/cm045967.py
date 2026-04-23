def _signal_process_tree_pid(process_group_id: int, *, force: bool) -> None:
    if process_group_id <= 0:
        return

    if os.name == "nt":
        command = ["taskkill", "/PID", str(process_group_id), "/T"]
        if force:
            command.append("/F")
        try:
            subprocess.run(
                command,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as exc:
            logger.debug(
                "Failed to signal managed MinerU process tree {} on Windows: {}",
                process_group_id,
                exc,
            )
        return

    sig = signal.SIGKILL if force else signal.SIGTERM
    try:
        os.killpg(process_group_id, sig)
    except ProcessLookupError:
        return
    except OSError as exc:
        logger.debug(
            "Failed to signal managed MinerU process group {}: {}",
            process_group_id,
            exc,
        )