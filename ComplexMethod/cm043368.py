def upload_cmd(profile_name: str, name: str, level: str, no_shrink: bool):
    """Upload a browser profile to Crawl4AI Cloud.

    The profile will be shrunk to remove caches before uploading.
    Use --no-shrink to upload the profile as-is.

    Examples:
      crwl cloud profiles upload my_profile
      crwl cloud profiles upload my_profile --name github-auth
      crwl cloud profiles upload my_profile --level minimal
      crwl cloud profiles upload my_profile --no-shrink
    """
    api_key, api_url = require_auth()

    # Find the profile
    profiler = BrowserProfiler()
    profile_path = profiler.get_profile_path(profile_name)

    if not profile_path:
        console.print(f"[red]Profile not found: {profile_name}[/red]")
        console.print("\nAvailable profiles:")
        for p in profiler.list_profiles():
            console.print(f"  - {p['name']}")
        sys.exit(1)

    cloud_name = name or profile_name

    console.print(f"\n[cyan]Uploading profile:[/cyan] {profile_name}")
    console.print(f"[cyan]Cloud name:[/cyan] {cloud_name}")

    # Step 1: Shrink (unless --no-shrink)
    if not no_shrink:
        console.print(f"\n[dim][1/4] Shrinking profile ({level})...[/dim]")
        try:
            result = profiler.shrink(profile_name, ShrinkLevel(level), dry_run=False)
            console.print(f"      Freed: {_format_size(result['bytes_freed'])}")
            if result.get("size_after"):
                console.print(f"      Size: {_format_size(result['size_after'])}")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not shrink profile: {e}[/yellow]")
    else:
        console.print("\n[dim][1/4] Skipping shrink...[/dim]")

    # Step 2: Package as tar.gz
    console.print("[dim][2/4] Packaging profile...[/dim]")

    temp_dir = Path(tempfile.mkdtemp(prefix="crawl4ai_upload_"))
    tar_path = temp_dir / f"{cloud_name}.tar.gz"

    try:
        with tarfile.open(tar_path, "w:gz") as tar:
            # Add profile contents (not the directory itself)
            for item in Path(profile_path).iterdir():
                tar.add(item, arcname=item.name)

        size_bytes = tar_path.stat().st_size
        console.print(f"      Created: {tar_path.name} ({_format_size(size_bytes)})")

        # Step 3: Upload
        console.print("[dim][3/4] Uploading to cloud...[/dim]")

        with open(tar_path, "rb") as f:
            response = httpx.post(
                f"{api_url}/v1/profiles",
                headers={"X-API-Key": api_key},
                files={"file": (f"{cloud_name}.tar.gz", f, "application/gzip")},
                data={"name": cloud_name},
                timeout=120.0
            )

        if response.status_code == 409:
            console.print(f"[red]Profile '{cloud_name}' already exists in cloud.[/red]")
            console.print("Use --name to specify a different name, or delete the existing profile first.")
            sys.exit(1)
        elif response.status_code == 400:
            error = response.json().get("detail", "Unknown error")
            console.print(f"[red]Upload rejected: {error}[/red]")
            sys.exit(1)
        elif response.status_code != 200:
            console.print(f"[red]Upload failed: {response.status_code}[/red]")
            console.print(response.text)
            sys.exit(1)

        result = response.json()
        profile_id = result["id"]

        console.print("[dim][4/4] Done![/dim]")

        # Success output
        console.print(Panel(
            f"[green]Profile uploaded successfully![/green]\n\n"
            f"Profile ID: [cyan]{profile_id}[/cyan]\n"
            f"Name: [blue]{cloud_name}[/blue]\n"
            f"Size: {_format_size(size_bytes)}\n\n"
            f"[dim]Use in API:[/dim]\n"
            f'  {{"browser_config": {{"profile_id": "{profile_id}"}}}}',
            title="Upload Complete",
            border_style="green"
        ))

        if result.get("scan_warnings"):
            console.print("\n[yellow]Scan warnings:[/yellow]")
            for warning in result["scan_warnings"]:
                console.print(f"  - {warning}")

    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)