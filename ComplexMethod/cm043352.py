def cdp_cmd(user_data_dir: Optional[str], port: int, browser_type: str, headless: bool, incognito: bool):
    """Launch a standalone browser with CDP debugging enabled

    This command launches a browser with Chrome DevTools Protocol (CDP) debugging enabled,
    prints the CDP URL, and keeps the browser running until you press 'q'.

    The CDP URL can be used for various automation and debugging tasks.

    Examples:
        # Launch Chromium with CDP on default port 9222
        crwl cdp

        # Use a specific directory for browser data and custom port
        crwl cdp --user-data-dir ~/browser-data --port 9223

        # Launch in headless mode
        crwl cdp --headless

        # Launch in incognito mode (ignores user-data-dir)
        crwl cdp --incognito
    """
    profiler = BrowserProfiler()

    try:
        # Handle data directory
        data_dir = None
        if not incognito and user_data_dir:
            # Expand user path (~/something)
            expanded_path = os.path.expanduser(user_data_dir)

            # Create directory if it doesn't exist
            if not os.path.exists(expanded_path):
                console.print(f"[yellow]Directory '{expanded_path}' doesn't exist. Creating it.[/yellow]")
                os.makedirs(expanded_path, exist_ok=True)

            data_dir = expanded_path

        # Print launch info
        console.print(Panel(
            f"[cyan]Launching browser with CDP debugging[/cyan]\n\n"
            f"Browser type: [green]{browser_type}[/green]\n"
            f"Debugging port: [yellow]{port}[/yellow]\n"
            f"User data directory: [cyan]{data_dir or 'Temporary directory'}[/cyan]\n"
            f"Headless: [cyan]{'Yes' if headless else 'No'}[/cyan]\n"
            f"Incognito: [cyan]{'Yes' if incognito else 'No'}[/cyan]\n\n"
            f"[yellow]Press 'q' to quit when done[/yellow]",
            title="CDP Browser",
            border_style="cyan"
        ))

        # Run the browser
        cdp_url = anyio.run(
            profiler.launch_standalone_browser,
            browser_type,
            data_dir,
            port,
            headless
        )

        if not cdp_url:
            console.print("[red]Failed to launch browser or get CDP URL[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error launching CDP browser: {str(e)}[/red]")
        sys.exit(1)