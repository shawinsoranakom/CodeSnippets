def shrink_cmd(profile_name: str, level: str, dry_run: bool):
    """Shrink a browser profile to reduce storage.

    Removes cache, history, and other non-essential data while preserving
    authentication (cookies, localStorage, IndexedDB).

    Shrink levels:
      light      - Remove caches only
      medium     - Remove caches + history
      aggressive - Keep only auth data (recommended)
      minimal    - Keep only cookies + localStorage

    Examples:
      crwl shrink my_profile
      crwl shrink my_profile --level minimal
      crwl shrink my_profile --dry-run
    """
    profiler = BrowserProfiler()

    try:
        result = profiler.shrink(profile_name, ShrinkLevel(level), dry_run)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    # Display results
    action = "Would remove" if dry_run else "Removed"
    console.print(f"\n[cyan]Shrink Results ({level.upper()}):[/cyan]")
    console.print(f"  {action}: {len(result['removed'])} items")
    console.print(f"  Kept: {len(result['kept'])} items")
    console.print(f"  Space freed: {_format_size(result['bytes_freed'])}")

    if result.get("size_before"):
        console.print(f"  Size before: {_format_size(result['size_before'])}")
    if result.get("size_after"):
        console.print(f"  Size after: {_format_size(result['size_after'])}")

    if result["errors"]:
        console.print(f"\n[red]Errors ({len(result['errors'])}):[/red]")
        for err in result["errors"]:
            console.print(f"  - {err}")

    if dry_run:
        console.print("\n[yellow]Dry run - no files were actually removed.[/yellow]")