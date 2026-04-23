def browser_view_cmd(url: Optional[str]):
    """
    Open a visible window of the builtin browser

    This command connects to the running builtin browser and opens a visible window,
    allowing you to see what the browser is currently viewing or navigate to a URL.
    """
    profiler = BrowserProfiler()

    try:
        # First check if browser is running
        status = anyio.run(profiler.get_builtin_browser_status)
        if not status["running"]:
            console.print(Panel(
                "[yellow]No builtin browser is currently running[/yellow]\n\n"
                "Use 'crwl browser start' to start a builtin browser first",
                title="Builtin Browser View",
                border_style="yellow"
            ))
            return

        info = status["info"]
        cdp_url = info["cdp_url"]

        console.print(Panel(
            f"[cyan]Opening visible window connected to builtin browser[/cyan]\n\n"
            f"CDP URL: [green]{cdp_url}[/green]\n"
            f"URL to load: [yellow]{url or 'about:blank'}[/yellow]",
            title="Builtin Browser View",
            border_style="cyan"
        ))

        # Use the CDP URL to launch a new visible window
        import subprocess
        import os

        # Determine the browser command based on platform
        if sys.platform == "darwin":  # macOS
            browser_cmd = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
        elif sys.platform == "win32":  # Windows
            browser_cmd = ["C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"]
        else:  # Linux
            browser_cmd = ["google-chrome"]

        # Add arguments
        browser_args = [
            f"--remote-debugging-port={info['debugging_port']}",
            "--remote-debugging-address=localhost",
            "--no-first-run",
            "--no-default-browser-check"
        ]

        # Add URL if provided
        if url:
            browser_args.append(url)

        # Launch browser
        try:
            subprocess.Popen(browser_cmd + browser_args)
            console.print("[green]Browser window opened. Close it when finished viewing.[/green]")
        except Exception as e:
            console.print(f"[red]Error launching browser: {str(e)}[/red]")
            console.print(f"[yellow]Try connecting manually to {cdp_url} in Chrome or using the '--remote-debugging-port' flag.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error viewing builtin browser: {str(e)}[/red]")
        sys.exit(1)