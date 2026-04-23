def _print_test_failure(self, test: TestResult) -> None:
        """Print a single test failure."""
        if RICH_AVAILABLE:
            tree = Tree(f"[red]{test.test_name}[/red]")
            tree.add(f"[dim]Task:[/dim] {test.task[:80]}...")
            tree.add(f"[dim]Steps:[/dim] {test.n_steps}")
            tree.add(f"[dim]Cost:[/dim] ${test.total_cost:.4f}")
            patterns = ", ".join(p.value for p in test.patterns_detected)
            tree.add(f"[dim]Patterns:[/dim] {patterns}")

            tools = tree.add("[dim]Tool sequence:[/dim]")
            tool_seq = [s.tool_name for s in test.steps[:10]]
            tools.add(" -> ".join(tool_seq) + ("..." if len(test.steps) > 10 else ""))

            if test.fail_reason:
                reason = tree.add("[dim]Fail reason:[/dim]")
                reason.add(Text(test.fail_reason[:200], style="red"))

            self.console.print(tree)
        else:
            print(f"\n  {test.test_name}")
            print(f"    Task: {test.task[:80]}...")
            print(f"    Steps: {test.n_steps}, Cost: ${test.total_cost:.4f}")
            print(f"    Patterns: {', '.join(p.value for p in test.patterns_detected)}")
            tool_seq = [s.tool_name for s in test.steps[:10]]
            print(f"    Tools: {' -> '.join(tool_seq)}")
            if test.fail_reason:
                print(f"    Fail reason: {test.fail_reason[:200]}")