def _list_tests(self) -> None:
        """List all failed tests."""
        all_tests = set()
        for analysis in self.strategies.values():
            for test in analysis.failed_tests:
                all_tests.add(test.test_name)

        if RICH_AVAILABLE:
            table = Table(title="Failed Tests Across Strategies")
            table.add_column("Test", style="cyan")
            for strategy in self.strategies.keys():
                table.add_column(strategy, justify="center")

            for test_name in sorted(all_tests):
                row = [test_name]
                for strategy in self.strategies.keys():
                    if (
                        test_name in self.test_comparison
                        and strategy in self.test_comparison[test_name]
                    ):
                        row.append("[red]FAIL[/red]")
                    else:
                        row.append("[green]PASS[/green]")
                table.add_row(*row)

            self.console.print(table)
        else:
            print("\n=== Failed Tests ===")
            for test_name in sorted(all_tests):
                print(f"  {test_name}")