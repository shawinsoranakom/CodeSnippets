def browser_restart_cmd(browser_type: Optional[str], port: Optional[int], headless: Optional[bool]):
    """Restart the builtin browser

    Stops the current builtin browser if running and starts a new one.
    By default, uses the same configuration as the current browser.
    """
    profiler = BrowserProfiler()

    try:
        # First check if browser is running and get its config
        status = anyio.run(profiler.get_builtin_browser_status)
        current_config = {}

        if status["running"]:
            info = status["info"]
            current_config = {
                "browser_type": info["browser_type"],
                "port": info["debugging_port"],
                "headless": True  # Default assumption
            }

            # Stop the browser
            console.print(Panel(
                "[cyan]Stopping current builtin browser...[/cyan]",
                title="Builtin Browser Restart", 
                border_style="cyan"
            ))

            success = anyio.run(profiler.kill_builtin_browser)
            if not success:
                console.print(Panel(
                    "[red]Failed to stop current browser[/red]",
                    title="Builtin Browser Restart",
                    border_style="red"
                ))
                sys.exit(1)

        # Use provided options or defaults from current config
        browser_type = browser_type or current_config.get("browser_type", "chromium")
        port = port or current_config.get("port", 9222)
        headless = headless if headless is not None else current_config.get("headless", True)

        # Start a new browser
        console.print(Panel(
            f"[cyan]Starting new builtin browser[/cyan]\n\n"
            f"Browser type: [green]{browser_type}[/green]\n"
            f"Debugging port: [yellow]{port}[/yellow]\n"
            f"Headless: [cyan]{'Yes' if headless else 'No'}[/cyan]",
            title="Builtin Browser Restart",
            border_style="cyan"
        ))

        cdp_url = anyio.run(
            profiler.launch_builtin_browser,
            browser_type,
            port,
            headless
        )

        if cdp_url:
            console.print(Panel(
                f"[green]Builtin browser restarted successfully[/green]\n\n"
                f"CDP URL: [cyan]{cdp_url}[/cyan]",
                title="Builtin Browser Restart",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[red]Failed to restart builtin browser[/red]",
                title="Builtin Browser Restart",
                border_style="red"
            ))
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error restarting builtin browser: {str(e)}[/red]")
        sys.exit(1)