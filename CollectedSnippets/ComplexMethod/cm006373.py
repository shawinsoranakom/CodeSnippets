def complete_step(self, step_index: int, *, success: bool = True) -> None:
        """Complete a step and stop its animation."""
        if step_index >= len(self.steps):
            return

        step = self.steps[step_index]
        step["status"] = "completed" if success else "failed"
        step["end_time"] = time.time()

        # Stop animation
        self._stop_animation = True
        if self._animation_thread and self._animation_thread.is_alive():
            self._animation_thread.join(timeout=0.5)

        self.running = False

        # Clear the current line and print final result
        sys.stdout.write("\r")

        if success:
            icon = click.style(self._success_icon, fg="green", bold=True)
            title = click.style(step["title"], fg="green")
        else:
            icon = click.style(self._failure_icon, fg="red", bold=True)
            title = click.style(step["title"], fg="red")

        duration = ""
        if step["start_time"] and step["end_time"]:
            elapsed = step["end_time"] - step["start_time"]
            if self.verbose and elapsed > MIN_DURATION_THRESHOLD:  # Only show duration if verbose and > 100ms
                duration = click.style(f" ({elapsed:.2f}s)", fg="bright_black")

        line = f"{icon} {title}{duration}"
        click.echo(line)