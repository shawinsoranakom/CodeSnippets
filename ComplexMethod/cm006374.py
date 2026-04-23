def print_summary(self) -> None:
        """Print a summary of all completed steps."""
        if not self.verbose:
            return

        completed_steps = [s for s in self.steps if s["status"] in ["completed", "failed"]]
        if not completed_steps:
            return

        total_time = sum(
            (s["end_time"] - s["start_time"]) for s in completed_steps if s["start_time"] and s["end_time"]
        )

        click.echo()
        click.echo(click.style(f"Total initialization time: {total_time:.2f}s", fg="bright_black"))