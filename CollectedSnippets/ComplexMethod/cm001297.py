def render_recent_completions(self, n: int = 5) -> Panel:
        """Render panel showing recent completions."""
        recent = self.completed[-n:] if self.completed else []

        if not recent:
            content = Text("No completions yet", style="dim")
        else:
            lines = []
            for result in reversed(recent):
                # Determine status icon and style
                if result.success:
                    status = Text("\u2713", style="green")
                elif result.timed_out and result.score >= 0.9:
                    status = Text("\u29D6", style="yellow")  # Hourglass - would pass
                elif result.timed_out:
                    status = Text("\u29D6", style="yellow")  # Hourglass
                else:
                    status = Text("\u2717", style="red")

                # Build suffix for special cases
                suffix = f" ({result.n_steps} steps)"
                if result.timed_out and result.score >= 0.9:
                    suffix = f" ({result.n_steps} steps) [yellow]would pass[/yellow]"

                line = Text.assemble(
                    ("  ", ""),
                    status,
                    (" ", ""),
                    (f"[{result.config_name}] ", "dim"),
                    (result.challenge_name, "white"),
                )
                # Handle markup in suffix separately
                if result.timed_out and result.score >= 0.9:
                    line.append(f" ({result.n_steps} steps) ", style="dim")
                    line.append("would pass", style="yellow")
                else:
                    line.append(suffix, style="dim")
                lines.append(line)
            content = Group(*lines)

        return Panel(
            content,
            title="[bold]Recent Completions[/bold]",
            border_style="green" if self.completed else "dim",
        )