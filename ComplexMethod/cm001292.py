def export_markdown(self, output_path: Optional[Path] = None) -> str:
        """Export analysis to markdown format."""
        lines = []
        lines.append("# Benchmark Failure Analysis Report")
        lines.append(f"\nGenerated: {datetime.now().isoformat()}\n")

        # Summary table
        lines.append("## Strategy Comparison\n")
        lines.append(
            "| Strategy | Tests | Passed | Failed | Success % | Avg Steps | Cost |"
        )
        lines.append(
            "|----------|-------|--------|--------|-----------|-----------|------|"
        )
        for name, analysis in sorted(
            self.strategies.items(), key=lambda x: x[1].success_rate, reverse=True
        ):
            row = (
                f"| {name} | {analysis.total_tests} | {analysis.passed} "
                f"| {analysis.failed} | {analysis.success_rate:.1f}% "
                f"| {analysis.avg_steps:.1f} | ${analysis.total_cost:.4f} |"
            )
            lines.append(row)

        # Pattern analysis
        lines.append("\n## Failure Patterns\n")
        all_patterns = Counter()
        for analysis in self.strategies.values():
            for test in analysis.failed_tests:
                for pattern in test.patterns_detected:
                    all_patterns[pattern] += 1

        for pattern, count in all_patterns.most_common():
            lines.append(f"- **{pattern.value}**: {count} occurrences")

        # Failed tests by strategy
        lines.append("\n## Failed Tests by Strategy\n")
        for name, analysis in self.strategies.items():
            if not analysis.failed_tests:
                continue
            lines.append(f"\n### {name}\n")
            for test in analysis.failed_tests:
                lines.append(f"#### {test.test_name}\n")
                lines.append(f"- **Task**: {test.task[:100]}...")
                lines.append(f"- **Steps**: {test.n_steps}")
                patterns = ", ".join(p.value for p in test.patterns_detected)
                lines.append(f"- **Patterns**: {patterns}")
                tools = " -> ".join(s.tool_name for s in test.steps[:8])
                lines.append(f"- **Tool sequence**: {tools}")
                if test.fail_reason:
                    lines.append(f"- **Fail reason**: {test.fail_reason[:150]}...")
                lines.append("")

        content = "\n".join(lines)

        if output_path:
            output_path.write_text(content)
            self._print(
                f"Markdown report saved to: {output_path}"
                if not RICH_AVAILABLE
                else f"[green]Markdown report saved to: {output_path}[/green]"
            )

        return content