def login_command(
    *,
    env: str | None,
    environments_file: str | None,
    target: str | None,
    api_key: str | None,
) -> None:
    sdk = load_sdk("login")

    from lfx.config import ConfigError, resolve_environment

    try:
        env_cfg = resolve_environment(
            env,
            target=target,
            api_key=api_key,
            environments_file=environments_file,
        )
    except ConfigError as exc:
        err_console.print(f"[red]Configuration error:[/red] {exc}")
        raise typer.Exit(1) from exc

    # ------------------------------------------------------------------
    # Key guidance (before probing)
    # ------------------------------------------------------------------
    key_env_name: str | None = None
    if env_cfg.api_key is None and env_cfg.name not in ("__inline__", "__env__"):
        key_env_name = _api_key_env_name(env_cfg.name, environments_file)

    if env_cfg.api_key is None:
        warning_parts = ["[yellow]Warning:[/yellow] No API key configured."]
        if key_env_name:
            warning_parts.append(f"  Set [bold]export {key_env_name}=<your-key>[/bold] then retry.")
        else:
            warning_parts.append("  Add [bold]api_key_env: LANGFLOW_<ENV>_API_KEY[/bold] to your config,")
            warning_parts.append("  then set that environment variable to your API key.")
        for line in warning_parts:
            err_console.print(line)

    # ------------------------------------------------------------------
    # Probe the connection
    # ------------------------------------------------------------------
    client = sdk.Client(base_url=env_cfg.url, api_key=env_cfg.api_key)

    console.print(f"[dim]Connecting to[/dim] {env_cfg.url} …")
    ok, msg, _flow_count = _probe_connection(client, sdk)

    if not ok:
        if msg == "auth":
            err_console.print()
            err_console.print("[red bold]✗ Authentication failed.[/red bold]")
            err_console.print(f"  URL:  {env_cfg.url}")
            if env_cfg.api_key:
                err_console.print(f"  Key:  {_mask_key(env_cfg.api_key)}")
            err_console.print()
            err_console.print("[bold]How to fix:[/bold]")
            if key_env_name:
                err_console.print("  1. Open Langflow → Settings → API Keys → Create a new key")
                err_console.print(f"  2. [bold]export {key_env_name}=<your-new-key>[/bold]")
            elif env_cfg.name not in ("__inline__", "__env__"):
                err_console.print("  1. Open Langflow → Settings → API Keys → Create a new key")
                err_console.print("  2. Pass [bold]--api-key <key>[/bold] or configure api_key_env in your YAML")
            else:
                err_console.print("  1. Open Langflow → Settings → API Keys → Create a new key")
                err_console.print("  2. Pass [bold]--api-key <key>[/bold]")
            raise typer.Exit(1)

        if msg.startswith("connection:"):
            err_console.print()
            err_console.print("[red bold]✗ Cannot connect.[/red bold]")
            err_console.print(f"  URL: {env_cfg.url}")
            err_console.print()
            err_console.print("[bold]How to fix:[/bold]")
            err_console.print("  • Make sure your Langflow instance is running")
            err_console.print("  • Check the URL in your .lfx/environments.yaml")
            err_console.print("  • If running locally: [bold]langflow run[/bold] or [bold]lfx serve <flow.json>[/bold]")
            raise typer.Exit(1)

        # Generic HTTP or other error
        err_console.print(f"\n[red bold]✗ Request failed:[/red bold] {msg.split(':', 1)[-1]}")
        raise typer.Exit(1)

    # ------------------------------------------------------------------
    # Success
    # ------------------------------------------------------------------
    masked_key = _mask_key(env_cfg.api_key) if env_cfg.api_key else "[dim](none)[/dim]"

    key_source = ""
    if key_env_name and env_cfg.api_key:
        key_source = f"  [dim]from env var {key_env_name}[/dim]"
    elif os.environ.get("LANGFLOW_API_KEY") == env_cfg.api_key and env_cfg.api_key:
        key_source = "  [dim]from LANGFLOW_API_KEY[/dim]"

    env_label = env_cfg.name if env_cfg.name not in ("__inline__", "__env__") else "(inline)"

    console.print()
    console.print(
        Panel.fit(
            f"[bold green]✓ Connected successfully![/bold green]\n\n"
            f"[bold]Environment:[/bold] {env_label}\n"
            f"[bold]URL:[/bold]         {env_cfg.url}\n"
            f"[bold]API key:[/bold]     {masked_key}{key_source}",
            title="[bold blue]lfx login[/bold blue]",
            border_style="green",
        )
    )

    if not env_cfg.api_key:
        console.print()
        console.print("[dim]Note: connected without an API key (anonymous access).[/dim]")
        console.print("[dim]Some operations may fail. Add api_key_env to your config.[/dim]")

    if env_cfg.name in ("__inline__", "__env__") and env_cfg.api_key:
        console.print()
        console.print("[dim]Tip: to avoid passing credentials each time, add to .lfx/environments.yaml:[/dim]")
        env_display = env or "myenv"
        console.print("[dim]  environments:[/dim]")
        console.print(f"[dim]    {env_display}:[/dim]")
        console.print(f"[dim]      url: {env_cfg.url}[/dim]")
        console.print(f"[dim]      api_key_env: LANGFLOW_{env_display.upper()}_API_KEY[/dim]")