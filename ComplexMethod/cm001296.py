def render_summary_table(self) -> Table:
        """Render summary table of results by configuration."""
        table = Table(title="Results by Configuration", show_header=True)
        table.add_column("Configuration", style="cyan")
        table.add_column("Passed", justify="right", style="green")
        table.add_column("Would Pass", justify="right", style="yellow")
        table.add_column("Failed", justify="right", style="red")
        table.add_column("Rate", justify="right")
        table.add_column("Cost", justify="right", style="yellow")

        for config_name, results in sorted(self.results_by_config.items()):
            if not results:
                continue
            passed = sum(1 for r in results if r.success)
            would_pass = sum(1 for r in results if r.timed_out and r.score >= 0.9)
            failed = len(results) - passed - would_pass
            # Rate includes "would pass" since those are correct solutions
            effective_passed = passed + would_pass
            rate = (effective_passed / len(results) * 100) if results else 0
            cost = sum(r.cost for r in results)

            rate_style = "green" if rate >= 75 else "yellow" if rate >= 50 else "red"
            table.add_row(
                config_name,
                str(passed),
                str(would_pass) if would_pass > 0 else "-",
                str(failed),
                f"[{rate_style}]{rate:.1f}%[/{rate_style}]",
                f"${cost:.4f}",
            )

        return table