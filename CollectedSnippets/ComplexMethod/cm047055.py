def stop():
    """Stop a running Unsloth Studio server.

    Reads the PID from ~/.unsloth/studio/studio.pid and sends SIGTERM
    (or TerminateProcess on Windows) to shut it down gracefully.
    """
    import signal as _signal

    if not _PID_FILE.is_file():
        typer.echo("No running Studio server found (no PID file).")
        raise typer.Exit(0)

    pid_text = _PID_FILE.read_text().strip()
    if not pid_text.isdigit():
        typer.echo(f"Invalid PID file contents: {pid_text}")
        _PID_FILE.unlink(missing_ok = True)
        raise typer.Exit(1)

    pid = int(pid_text)

    # Check if the process is still alive
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        typer.echo(
            f"Studio server (PID {pid}) is not running. Cleaning up stale PID file."
        )
        _PID_FILE.unlink(missing_ok = True)
        raise typer.Exit(0)
    except PermissionError:
        pass  # process exists but we may not own it; try to signal anyway

    # Send SIGTERM (graceful shutdown) or TerminateProcess on Windows
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], check = True)
        else:
            os.kill(pid, _signal.SIGTERM)
        typer.echo(f"Sent shutdown signal to Studio server (PID {pid}).")
    except ProcessLookupError:
        typer.echo(f"Studio server (PID {pid}) already exited.")
        _PID_FILE.unlink(missing_ok = True)
        raise typer.Exit(0)
    except Exception as e:
        typer.echo(f"Failed to stop Studio server (PID {pid}): {e}", err = True)
        raise typer.Exit(1)

    # Wait briefly for the process to exit and clean up
    for _ in range(10):
        time.sleep(0.5)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            _PID_FILE.unlink(missing_ok = True)
            typer.echo("Studio server stopped.")
            raise typer.Exit(0)
        except PermissionError:
            break

    typer.echo("Studio server is shutting down (may take a few seconds).")