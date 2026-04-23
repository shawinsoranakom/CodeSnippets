def studio_default(
    ctx: typer.Context,
    port: int = typer.Option(8888, "--port", "-p"),
    host: str = typer.Option("0.0.0.0", "--host", "-H"),
    frontend: Optional[Path] = typer.Option(None, "--frontend", "-f"),
    silent: bool = typer.Option(False, "--silent", "-q"),
):
    """Launch the Unsloth Studio server."""
    if ctx.invoked_subcommand is not None:
        return

    # Always use the studio venv if it exists and we're not already in it
    studio_venv_dir = STUDIO_HOME / "unsloth_studio"
    in_studio_venv = sys.prefix.startswith(str(studio_venv_dir))

    if not in_studio_venv:
        studio_python = _studio_venv_python()
        run_py = _find_run_py()
        if studio_python and run_py:
            if not silent:
                typer.echo("Launching Unsloth Studio... Please wait...")
            args = [
                str(studio_python),
                str(run_py),
                "--host",
                host,
                "--port",
                str(port),
            ]
            if frontend:
                args.extend(["--frontend", str(frontend)])
            if silent:
                args.append("--silent")
            # On Windows, os.execvp() spawns a child but the parent lingers,
            # so Ctrl+C only kills the parent leaving the child orphaned.
            # Use subprocess.run() on Windows so the parent waits for the child.
            if sys.platform == "win32":
                import subprocess as _sp

                proc = _sp.Popen(args)
                try:
                    rc = proc.wait()
                except KeyboardInterrupt:
                    # Child has its own signal handler — let it finish
                    rc = proc.wait()
                if rc != 0:
                    typer.echo(
                        f"\nError: Studio server exited unexpectedly (code {rc}).",
                        err = True,
                    )
                    typer.echo(
                        "Check the error above. If a package is missing, "
                        "re-run: unsloth studio setup",
                        err = True,
                    )
                raise typer.Exit(rc)
            else:
                os.execvp(str(studio_python), args)
        else:
            typer.echo("Studio not set up. Run install.sh first.")
            raise typer.Exit(1)

    from studio.backend.run import run_server

    if not silent:
        from studio.backend.run import _resolve_external_ip

        display_host = _resolve_external_ip() if host == "0.0.0.0" else host
        typer.echo(f"Starting Unsloth Studio on http://{display_host}:{port}")

    run_kwargs = dict(host = host, port = port, silent = silent)
    if frontend is not None:
        run_kwargs["frontend_path"] = frontend
    run_server(**run_kwargs)

    from studio.backend.run import _shutdown_event

    try:
        if _shutdown_event is not None:
            # NOTE: Event.wait() without a timeout blocks at the C level
            # on Linux, preventing Python from delivering SIGINT (Ctrl+C).
            while not _shutdown_event.is_set():
                _shutdown_event.wait(timeout = 1)
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        from studio.backend.run import _graceful_shutdown, _server

        _graceful_shutdown(_server)
        typer.echo("\nShutting down...")