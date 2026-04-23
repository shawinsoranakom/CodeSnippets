def _print_completion_block(
        self,
        config_name: str,
        challenge_name: str,
        result: ChallengeResult,
        steps: list[tuple[int, str, str, bool]],
    ) -> None:
        """Print a copy-paste friendly completion block."""
        from datetime import datetime

        color = self.get_config_color(config_name)

        # Determine status display
        if result.success:
            status = "PASS"
            status_style = "green"
        elif result.timed_out and result.score >= 0.9:
            # Timed out but would have passed - show this clearly
            status = "TIMEOUT (would have passed)"
            status_style = "yellow"
        elif result.timed_out:
            status = "TIMEOUT"
            status_style = "yellow"
        else:
            status = "FAIL"
            status_style = "red"

        # Build challenge display with attempt if > 1
        challenge_display = challenge_name
        if result.attempt > 1:
            challenge_display = f"{challenge_name} (attempt {result.attempt})"

        # Generate timestamp for run identification
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Print header with full identification
        console.print()
        console.print(f"[{status_style}]{'═' * 70}[/{status_style}]")
        console.print(
            f"[{status_style} bold][{status}][/{status_style} bold] "
            f"[{color}]{config_name}[/{color}] - {challenge_display}"
        )
        run_id = f"{config_name}:{challenge_name}:{result.attempt}"
        console.print(f"[dim]Run ID: {run_id} @ {timestamp}[/dim]")
        console.print(f"[{status_style}]{'═' * 70}[/{status_style}]")

        # Print steps
        for step_num, tool_name, result_preview, is_error in steps:
            step_status = "[red]ERR[/red]" if is_error else "[green]OK[/green]"
            console.print(f"  Step {step_num}: {tool_name} {step_status}")
            if result_preview and (is_error or self.debug):
                # Indent the preview
                for line in result_preview.split("\n")[:3]:  # First 3 lines
                    console.print(f"    [dim]{line[:80]}[/dim]")

        # Print summary
        console.print()
        stats = (
            f"Steps: {result.n_steps} | Time: {result.run_time_seconds:.1f}s "
            f"| Cost: ${result.cost:.4f}"
        )
        console.print(f"  [dim]{stats}[/dim]")

        # Print error if any (skip generic timeout message since status shows it)
        if result.error_message and result.error_message != "Challenge timed out":
            console.print(f"  [red]Error: {result.error_message[:200]}[/red]")

        console.print(f"[{status_style}]{'─' * 70}[/{status_style}]")
        console.print()