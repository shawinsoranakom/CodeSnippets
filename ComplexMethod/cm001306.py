def state_reset(
    strategies: tuple[str, ...],
    models: tuple[str, ...],
    challenges: tuple[str, ...],
    reports_dir: Optional[Path],
):
    """Reset specific runs from saved state."""
    from .state import StateManager

    if not strategies and not models and not challenges:
        msg = "[red]Must specify --strategy, --model, or --challenge[/red]"
        console.print(msg)
        sys.exit(1)

    if reports_dir is None:
        reports_dir = Path.cwd() / "reports"

    state_manager = StateManager(reports_dir)
    total_reset = 0

    for strat in strategies:
        count = state_manager.reset_matching(strategy=strat)
        total_reset += count
        if count > 0:
            console.print(f"Reset {count} runs for strategy: {strat}")

    for model in models:
        count = state_manager.reset_matching(model=model)
        total_reset += count
        if count > 0:
            console.print(f"Reset {count} runs for model: {model}")

    for chal in challenges:
        count = state_manager.reset_matching(challenge=chal)
        total_reset += count
        if count > 0:
            console.print(f"Reset {count} runs for challenge: {chal}")

    if total_reset == 0:
        console.print("[dim]No matching runs found.[/dim]")
    else:
        console.print(f"\n[green]Total reset: {total_reset} runs[/green]")