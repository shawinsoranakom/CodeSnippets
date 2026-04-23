def auth_cmd(api_key: str, api_url: str, logout: bool, status: bool):
    """Authenticate with Crawl4AI Cloud.

    Your API key is saved locally in ~/.crawl4ai/global.yml

    To get an API key:
      1. Go to https://api.crawl4ai.com/dashboard
      2. Sign in or create an account
      3. Navigate to API Keys section
      4. Create a new key and copy it

    Examples:
      crwl cloud auth                    # Interactive authentication
      crwl cloud auth --api-key sk_...   # Provide key directly
      crwl cloud auth --status           # Check current status
      crwl cloud auth --logout           # Remove saved credentials
    """
    config = get_global_config()

    if status:
        current_key = config.get("CLOUD_API_KEY")
        current_url = config.get("CLOUD_API_URL", DEFAULT_CLOUD_API_URL)

        if current_key:
            # Mask the key for display
            masked = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "***"
            console.print(Panel(
                f"[green]Authenticated[/green]\n\n"
                f"API Key: [cyan]{masked}[/cyan]\n"
                f"API URL: [blue]{current_url}[/blue]",
                title="Cloud Auth Status",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[yellow]Not authenticated[/yellow]\n\n"
                "Run [cyan]crwl cloud auth[/cyan] to authenticate.\n\n"
                "Get your API key at:\n"
                "[blue]https://api.crawl4ai.com/dashboard[/blue]",
                title="Cloud Auth Status",
                border_style="yellow"
            ))
        return

    if logout:
        if "CLOUD_API_KEY" in config:
            del config["CLOUD_API_KEY"]
            save_global_config(config)
            console.print("[green]Logged out successfully.[/green]")
        else:
            console.print("[yellow]Not currently authenticated.[/yellow]")
        return

    # Interactive auth
    if not api_key:
        console.print(Panel(
            "[cyan]Crawl4AI Cloud Authentication[/cyan]\n\n"
            "To get your API key:\n"
            "  1. Go to [blue]https://api.crawl4ai.com/dashboard[/blue]\n"
            "  2. Sign in or create an account\n"
            "  3. Navigate to API Keys section\n"
            "  4. Create a new key and paste it below",
            title="Setup",
            border_style="cyan"
        ))
        api_key = click.prompt("\nEnter your API key", hide_input=True)

    if not api_key:
        console.print("[red]API key is required.[/red]")
        sys.exit(1)

    # Validate the key by making a test request
    test_url = api_url or config.get("CLOUD_API_URL", DEFAULT_CLOUD_API_URL)

    console.print("\n[dim]Validating API key...[/dim]")

    try:
        response = httpx.get(
            f"{test_url}/v1/profiles",
            headers={"X-API-Key": api_key},
            timeout=10.0
        )

        if response.status_code == 401:
            console.print("[red]Invalid API key.[/red]")
            sys.exit(1)
        elif response.status_code != 200:
            console.print(f"[red]Error validating key: {response.status_code}[/red]")
            sys.exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        sys.exit(1)

    # Save to config
    config["CLOUD_API_KEY"] = api_key
    if api_url:
        config["CLOUD_API_URL"] = api_url
    save_global_config(config)

    console.print("[green]Authentication successful![/green]")
    console.print(f"Credentials saved to [cyan]~/.crawl4ai/global.yml[/cyan]")