def list_cmd():
    """List all cloud profiles.

    Shows all profiles uploaded to your Crawl4AI Cloud account.
    """
    api_key, api_url = require_auth()

    console.print("\n[dim]Fetching profiles...[/dim]")

    try:
        response = httpx.get(
            f"{api_url}/v1/profiles",
            headers={"X-API-Key": api_key},
            timeout=30.0
        )

        if response.status_code != 200:
            console.print(f"[red]Error: {response.status_code}[/red]")
            console.print(response.text)
            sys.exit(1)

        data = response.json()
        profiles = data.get("profiles", [])

        if not profiles:
            console.print(Panel(
                "[yellow]No cloud profiles found.[/yellow]\n\n"
                "Upload a profile with:\n"
                "  [cyan]crwl cloud profiles upload <profile_name>[/cyan]",
                title="Cloud Profiles",
                border_style="yellow"
            ))
            return

        # Create table
        table = Table(title="Cloud Profiles")
        table.add_column("Name", style="cyan")
        table.add_column("Profile ID", style="dim")
        table.add_column("Size", justify="right")
        table.add_column("Created", style="green")
        table.add_column("Last Used", style="blue")

        for p in profiles:
            size = _format_size(p.get("size_bytes", 0)) if p.get("size_bytes") else "-"
            created = p.get("created_at", "-")[:10] if p.get("created_at") else "-"
            last_used = p.get("last_used_at", "-")[:10] if p.get("last_used_at") else "Never"

            table.add_row(
                p["name"],
                p["id"][:8] + "...",
                size,
                created,
                last_used
            )

        console.print(table)
        console.print(f"\nTotal: {len(profiles)} profile(s)")

    except httpx.RequestError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        sys.exit(1)