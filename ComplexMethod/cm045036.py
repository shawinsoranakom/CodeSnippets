def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        message = config.get("message", "Review required.")
        if isinstance(message, str) and "{{" in message:
            message = evaluate_expression(message, context)

        options = config.get("options", ["approve", "reject"])
        on_reject = config.get("on_reject", "abort")

        show_file = config.get("show_file")
        if show_file and isinstance(show_file, str) and "{{" in show_file:
            show_file = evaluate_expression(show_file, context)

        output = {
            "message": message,
            "options": options,
            "on_reject": on_reject,
            "show_file": show_file,
            "choice": None,
        }

        # Non-interactive: pause for later resume
        if not sys.stdin.isatty():
            return StepResult(status=StepStatus.PAUSED, output=output)

        # Interactive: prompt the user
        choice = self._prompt(message, options)
        output["choice"] = choice

        if choice in ("reject", "abort"):
            if on_reject == "abort":
                output["aborted"] = True
                return StepResult(
                    status=StepStatus.FAILED,
                    output=output,
                    error=f"Gate rejected by user at step {config.get('id', '?')!r}",
                )
            if on_reject == "retry":
                # Pause so the next resume re-executes this gate
                return StepResult(status=StepStatus.PAUSED, output=output)
            # on_reject == "skip" → completed, downstream steps decide
            return StepResult(status=StepStatus.COMPLETED, output=output)

        return StepResult(status=StepStatus.COMPLETED, output=output)