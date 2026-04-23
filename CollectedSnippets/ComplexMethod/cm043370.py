def delete_cmd(profile_name_or_id: str, yes: bool):
    """Delete a cloud profile.

    You can specify either the profile name or ID.

    Examples:
      crwl cloud profiles delete my_profile
      crwl cloud profiles delete abc123...
      crwl cloud profiles delete my_profile --yes
    """
    api_key, api_url = require_auth()

    # First, try to find the profile
    console.print("\n[dim]Finding profile...[/dim]")

    try:
        # List profiles to find by name
        response = httpx.get(
            f"{api_url}/v1/profiles",
            headers={"X-API-Key": api_key},
            timeout=30.0
        )

        if response.status_code != 200:
            console.print(f"[red]Error: {response.status_code}[/red]")
            sys.exit(1)

        profiles = response.json().get("profiles", [])

        # Find matching profile
        profile = None
        for p in profiles:
            if p["name"] == profile_name_or_id or p["id"] == profile_name_or_id or p["id"].startswith(profile_name_or_id):
                profile = p
                break

        if not profile:
            console.print(f"[red]Profile not found: {profile_name_or_id}[/red]")
            console.print("\nAvailable profiles:")
            for p in profiles:
                console.print(f"  - {p['name']} ({p['id'][:8]}...)")
            sys.exit(1)

        # Confirm deletion
        console.print(f"\nProfile: [cyan]{profile['name']}[/cyan]")
        console.print(f"ID: [dim]{profile['id']}[/dim]")

        if not yes:
            if not click.confirm("\nAre you sure you want to delete this profile?"):
                console.print("[yellow]Cancelled.[/yellow]")
                return

        # Delete
        console.print("\n[dim]Deleting...[/dim]")

        response = httpx.delete(
            f"{api_url}/v1/profiles/{profile['id']}",
            headers={"X-API-Key": api_key},
            timeout=30.0
        )

        if response.status_code == 404:
            console.print("[red]Profile not found (may have been already deleted).[/red]")
            sys.exit(1)
        elif response.status_code != 200:
            console.print(f"[red]Error: {response.status_code}[/red]")
            console.print(response.text)
            sys.exit(1)

        console.print(f"[green]Profile '{profile['name']}' deleted successfully.[/green]")

    except httpx.RequestError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        sys.exit(1)