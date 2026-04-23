def print_final_summary(self) -> None:
        """Print final summary after all benchmarks complete."""
        elapsed = (
            (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        )

        console.print()
        console.print("=" * 70)
        console.print("[bold]BENCHMARK COMPLETE[/bold]")
        console.print("=" * 70)
        console.print()

        # Summary table
        console.print(self.render_summary_table())

        # Overall stats
        total_passed = sum(1 for r in self.completed if r.success)
        total_would_pass = sum(
            1 for r in self.completed if r.timed_out and r.score >= 0.9
        )
        _total_failed = (  # noqa: F841
            len(self.completed) - total_passed - total_would_pass
        )
        total_cost = sum(r.cost for r in self.completed)
        # Include "would pass" in the effective rate
        effective_passed = total_passed + total_would_pass
        total_rate = (
            (effective_passed / len(self.completed) * 100) if self.completed else 0
        )

        console.print()
        if total_would_pass > 0:
            console.print(
                f"[bold]Total:[/bold] {total_passed}/{len(self.completed)} passed "
                f"[yellow](+{total_would_pass} would pass)[/yellow]"
            )
        else:
            console.print(
                f"[bold]Total:[/bold] {total_passed}/{len(self.completed)} passed"
            )
        console.print(f"[bold]Success Rate:[/bold] {total_rate:.1f}%")
        console.print(f"[bold]Total Cost:[/bold] ${total_cost:.4f}")
        console.print(f"[bold]Elapsed Time:[/bold] {elapsed:.1f}s")
        console.print()