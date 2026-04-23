def render_active_runs(self) -> Panel:
        """Render panel showing active runs with step history columns."""
        if not self.active_runs:
            content = Text("Waiting for runs to start...", style="dim")
            return Panel(
                content,
                title=f"[bold]Active Runs (0/{self.max_parallel})[/bold]",
                border_style="blue",
            )

        # Create a panel for each active run showing its step history
        panels = []
        for run_key, (config_name, challenge_name) in self.active_runs.items():
            color = self.get_config_color(config_name)
            steps = self.step_history.get(run_key, [])

            # Build step lines (show last 6 steps)
            lines = [Text(challenge_name, style="bold white")]
            for step_num, tool_name, _, is_error in steps[-6:]:
                status = "\u2717" if is_error else "\u2713"
                status_style = "red" if is_error else "green"
                lines.append(
                    Text.assemble(
                        (f"  {status} ", status_style),
                        (f"#{step_num} ", "dim"),
                        (tool_name, "white"),
                    )
                )

            # Add current step indicator
            current_step = self.active_steps.get(run_key, "")
            if current_step:
                lines.append(
                    Text.assemble(("  \u25cf ", "yellow"), (current_step, "dim"))
                )

            panel = Panel(
                Group(*lines),
                title=f"[{color}]{config_name}[/{color}]",
                border_style=color,
                width=30,
            )
            panels.append(panel)

        # Arrange panels in columns (up to 10 per row based on terminal width)
        # Each panel is ~30 chars wide, so calculate how many fit
        term_width = console.width or 120
        max_cols = min(10, max(1, term_width // 31))

        if len(panels) <= max_cols:
            content = Columns(panels, equal=True, expand=True)
        else:
            # Stack in rows
            rows = []
            for i in range(0, len(panels), max_cols):
                rows.append(Columns(panels[i : i + max_cols], equal=True, expand=True))
            content = Group(*rows)

        active = len(self.active_runs)
        title = f"[bold]Active Runs ({active}/{self.max_parallel})[/bold]"
        return Panel(content, title=title, border_style="blue")