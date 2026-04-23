def _show_step_detail(self, strategy: str, test_name: str, step_num: int) -> None:
        """Show detailed information about a specific step."""
        if strategy not in self.strategies:
            self._print(
                f"[red]Unknown strategy: {strategy}[/red]"
                if RICH_AVAILABLE
                else f"Unknown strategy: {strategy}"
            )
            return

        test = None
        for t in self.strategies[strategy].failed_tests:
            if t.test_name == test_name:
                test = t
                break

        if not test:
            self._print(
                f"[red]Test '{test_name}' not found in {strategy}[/red]"
                if RICH_AVAILABLE
                else f"Test '{test_name}' not found in {strategy}"
            )
            return

        if step_num < 1 or step_num > len(test.steps):
            self._print(
                f"[red]Step {step_num} out of range (1-{len(test.steps)})[/red]"
                if RICH_AVAILABLE
                else f"Step {step_num} out of range (1-{len(test.steps)})"
            )
            return

        step = test.steps[step_num - 1]

        if RICH_AVAILABLE:
            self.console.print(Panel(f"[bold]Step {step_num} Details[/bold]"))
            self.console.print(f"[cyan]Tool:[/cyan] {step.tool_name}")
            self.console.print(
                f"[cyan]Arguments:[/cyan] {json.dumps(step.tool_args, indent=2)}"
            )

            if step.thoughts:
                self.console.print("\n[cyan]Thoughts:[/cyan]")
                for key, value in step.thoughts.items():
                    self.console.print(f"  [dim]{key}:[/dim] {value}")

            if step.tool_result:
                result_str = json.dumps(step.tool_result, indent=2)[:500]
                self.console.print(f"\n[cyan]Result:[/cyan] {result_str}")

            self.console.print(
                f"\n[cyan]Cumulative Cost:[/cyan] ${step.cumulative_cost:.4f}"
            )
        else:
            print(f"\n=== Step {step_num} Details ===")
            print(f"Tool: {step.tool_name}")
            print(f"Arguments: {json.dumps(step.tool_args, indent=2)}")
            if step.thoughts:
                print("\nThoughts:")
                for key, value in step.thoughts.items():
                    print(f"  {key}: {value}")
            if step.tool_result:
                print(f"\nResult: {json.dumps(step.tool_result, indent=2)[:500]}")
            print(f"\nCumulative Cost: ${step.cumulative_cost:.4f}")