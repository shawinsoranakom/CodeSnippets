def list_challenges(challenges_dir: Optional[Path]):
    """List available challenges."""
    if challenges_dir is None:
        challenges_dir = find_challenges_dir()
        if challenges_dir is None:
            console.print(
                "[red]Could not find challenges directory. "
                "Please specify with --challenges-dir[/red]"
            )
            sys.exit(1)

    from .challenge_loader import ChallengeLoader

    loader = ChallengeLoader(challenges_dir)
    challenges = sorted(loader.load_all(), key=lambda c: c.name)

    console.print(f"\n[bold]Available Challenges ({len(challenges)})[/bold]\n")

    # Group by category
    by_category: dict[str, list[str]] = {}
    for c in challenges:
        for cat in c.category:
            if cat not in by_category:
                by_category[cat] = []
            if c.name not in by_category[cat]:
                by_category[cat].append(c.name)

    for cat in sorted(by_category.keys()):
        console.print(f"[cyan]{cat}[/cyan]: {', '.join(sorted(by_category[cat]))}")