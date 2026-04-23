def run(
    model: str = typer.Option(..., "--model", "-m", help = "Model path or HF repo"),
    gguf_variant: Optional[str] = typer.Option(
        None, "--gguf-variant", help = "GGUF quant variant (e.g. UD-Q4_K_XL)"
    ),
    max_seq_length: int = typer.Option(
        0, "--max-seq-length", help = "Max sequence length (0 = model default)"
    ),
    load_in_4bit: bool = typer.Option(True, "--load-in-4bit/--no-load-in-4bit"),
    api_key_name: str = typer.Option(
        "cli", "--api-key-name", help = "Label for the auto-generated API key"
    ),
    port: int = typer.Option(8888, "--port", "-p"),
    host: str = typer.Option("0.0.0.0", "--host", "-H"),
    frontend: Optional[Path] = typer.Option(None, "--frontend", "-f"),
    silent: bool = typer.Option(False, "--silent", "-q"),
):
    """Start Studio, load a model, and print an API key -- one-liner server.

    Example:
        unsloth studio run --model unsloth/Qwen3-1.7B-GGUF --gguf-variant UD-Q4_K_XL
    """
    # ── 1. Venv re-exec (same pattern as studio_default) ──────────────
    studio_venv_dir = STUDIO_HOME / "unsloth_studio"
    in_studio_venv = sys.prefix.startswith(str(studio_venv_dir))

    if not in_studio_venv:
        studio_python = _studio_venv_python()
        if not studio_python:
            typer.echo("Studio not set up. Run install.sh first.")
            raise typer.Exit(1)
        # Re-exec into the studio venv via its `unsloth` entry point
        studio_bin = studio_python.parent / "unsloth"
        if not studio_bin.is_file():
            typer.echo(
                "Studio venv missing 'unsloth' entry point. Re-run: unsloth studio setup"
            )
            raise typer.Exit(1)
        args = [
            str(studio_bin),
            "studio",
            "run",
            "--model",
            model,
            "--max-seq-length",
            str(max_seq_length),
            "--api-key-name",
            api_key_name,
            "--port",
            str(port),
            "--host",
            host,
        ]
        if gguf_variant:
            args.extend(["--gguf-variant", gguf_variant])
        if not load_in_4bit:
            args.append("--no-load-in-4bit")
        if frontend:
            args.extend(["--frontend", str(frontend)])
        if silent:
            args.append("--silent")

        if sys.platform == "win32":
            proc = subprocess.Popen(args)
            try:
                rc = proc.wait()
            except KeyboardInterrupt:
                rc = proc.wait()
            raise typer.Exit(rc)
        else:
            os.execvp(str(studio_bin), args)

    # ── 2. Start server (always suppress built-in banner) ─────────────
    from studio.backend.run import run_server, _resolve_external_ip

    run_kwargs = dict(host = host, port = port, silent = True, llama_parallel_slots = 4)
    if frontend is not None:
        run_kwargs["frontend_path"] = frontend
    app = run_server(**run_kwargs)
    actual_port = getattr(app.state, "server_port", port) or port

    # ── 3. Wait for server health ─────────────────────────────────────
    if not silent:
        typer.echo("Starting Unsloth Studio...")
    if not _wait_for_server(actual_port):
        typer.echo("Error: server did not become healthy within 30 seconds.", err = True)
        raise typer.Exit(1)

    # ── 4. Create API key in-process ──────────────────────────────────
    api_key = _create_api_key_inprocess(api_key_name)

    # ── 5. Load model via HTTP ────────────────────────────────────────
    if not silent:
        typer.echo(f"Loading model: {model}...")
    try:
        result = _load_model_via_http(
            port = actual_port,
            api_key = api_key,
            model = model,
            gguf_variant = gguf_variant,
            max_seq_length = max_seq_length,
            load_in_4bit = load_in_4bit,
        )
    except RuntimeError as exc:
        typer.echo(f"Error: {exc}", err = True)
        raise typer.Exit(1)

    loaded_model = result.get("model", model)
    display_variant = f" ({gguf_variant})" if gguf_variant else ""

    # ── 6. Print banner ───────────────────────────────────────────────
    display_host = _resolve_external_ip() if host == "0.0.0.0" else host
    base_url = f"http://{display_host}:{actual_port}"
    sdk_base_url = f"{base_url}/v1"

    if not silent:
        typer.echo("")
        typer.echo("=" * 56)
        typer.echo(f"  Unsloth Studio running at {base_url}")
        typer.echo(f"  Model loaded: {loaded_model}{display_variant}")
        typer.echo(f"  API Key:      {api_key}")
        typer.echo("")
        typer.echo("  OpenAI / Anthropic SDK base URL:")
        typer.echo(f"    {sdk_base_url}")
        typer.echo("=" * 56)
        typer.echo("")
        typer.echo("OpenAI Chat Completions:")
        typer.echo(f"  curl {sdk_base_url}/chat/completions \\")
        typer.echo(f'    -H "Authorization: Bearer {api_key}" \\')
        typer.echo('    -H "Content-Type: application/json" \\')
        typer.echo(
            """    -d '{"messages": [{"role": "user", "content": "Hello"}], "stream": true}'"""
        )
        typer.echo("")
        typer.echo("Anthropic Messages:")
        typer.echo(f"  curl {sdk_base_url}/messages \\")
        typer.echo(f'    -H "Authorization: Bearer {api_key}" \\')
        typer.echo('    -H "Content-Type: application/json" \\')
        typer.echo(
            """    -d '{"max_tokens": 256, "messages": [{"role": "user", "content": "Hello"}], "stream": true}'"""
        )
        typer.echo("")
        typer.echo("OpenAI Responses:")
        typer.echo(f"  curl {sdk_base_url}/responses \\")
        typer.echo(f'    -H "Authorization: Bearer {api_key}" \\')
        typer.echo('    -H "Content-Type: application/json" \\')
        typer.echo("""    -d '{"input": "Hello", "stream": true}'""")
        typer.echo("")

    # ── 7. Wait for Ctrl+C ────────────────────────────────────────────
    from studio.backend.run import _shutdown_event, _graceful_shutdown, _server

    try:
        if _shutdown_event is not None:
            while not _shutdown_event.is_set():
                _shutdown_event.wait(timeout = 1)
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        _graceful_shutdown(_server)
        typer.echo("\nShutting down...")