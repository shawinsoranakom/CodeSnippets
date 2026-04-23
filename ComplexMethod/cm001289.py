def interactive_mode(self) -> None:
        """Run interactive exploration mode."""
        if not RICH_AVAILABLE:
            print("Interactive mode requires the 'rich' library.")
            print("Install with: pip install rich")
            return

        while True:
            self.console.print("\n[bold]Interactive Failure Analysis[/bold]")
            self.console.print("Commands:")
            self.console.print("  [cyan]summary[/cyan] - Show overall summary")
            self.console.print("  [cyan]patterns[/cyan] - Show pattern analysis")
            self.console.print(
                "  [cyan]strategy <name>[/cyan] - Show failures for a strategy"
            )
            self.console.print(
                "  [cyan]test <name>[/cyan] - Compare test across strategies"
            )
            self.console.print(
                "  [cyan]step <strategy> <test> <n>[/cyan] - Show step details"
            )
            self.console.print("  [cyan]list tests[/cyan] - List all failed tests")
            self.console.print("  [cyan]list strategies[/cyan] - List strategies")
            self.console.print("  [cyan]quit[/cyan] - Exit")

            cmd = Prompt.ask("\n[bold]>>[/bold]").strip().lower()

            if cmd == "quit" or cmd == "q":
                break
            elif cmd == "summary":
                self.print_summary()
            elif cmd == "patterns":
                self.print_pattern_analysis()
            elif cmd.startswith("strategy "):
                strategy = cmd.split(" ", 1)[1]
                if strategy in self.strategies:
                    self.print_failed_tests(strategy)
                else:
                    self.console.print(f"[red]Unknown strategy: {strategy}[/red]")
            elif cmd.startswith("test "):
                test_name = cmd.split(" ", 1)[1]
                self.compare_test(test_name)
            elif cmd.startswith("step "):
                parts = cmd.split()
                if len(parts) >= 4:
                    strategy = parts[1]
                    test_name = parts[2]
                    step_num = int(parts[3])
                    self._show_step_detail(strategy, test_name, step_num)
                else:
                    self.console.print(
                        "[red]Usage: step <strategy> <test> <step_num>[/red]"
                    )
            elif cmd == "list tests":
                self._list_tests()
            elif cmd == "list strategies":
                self.console.print(", ".join(self.strategies.keys()))
            else:
                self.console.print(f"[red]Unknown command: {cmd}[/red]")