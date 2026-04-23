def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        command = config.get("command", "")
        input_data = config.get("input", {})

        # Resolve expressions in input
        resolved_input: dict[str, Any] = {}
        for key, value in input_data.items():
            resolved_input[key] = evaluate_expression(value, context)

        # Resolve integration (step → workflow default → project default)
        integration = config.get("integration") or context.default_integration
        if integration and isinstance(integration, str) and "{{" in integration:
            integration = evaluate_expression(integration, context)

        # Resolve model
        model = config.get("model") or context.default_model
        if model and isinstance(model, str) and "{{" in model:
            model = evaluate_expression(model, context)

        # Merge options (workflow defaults ← step overrides)
        options = dict(context.default_options)
        step_options = config.get("options", {})
        if step_options:
            options.update(step_options)

        # Attempt CLI dispatch
        args_str = str(resolved_input.get("args", ""))
        dispatch_result = self._try_dispatch(
            command, integration, model, args_str, context
        )

        output: dict[str, Any] = {
            "command": command,
            "integration": integration,
            "model": model,
            "options": options,
            "input": resolved_input,
        }

        if dispatch_result is not None:
            output["exit_code"] = dispatch_result["exit_code"]
            output["stdout"] = dispatch_result["stdout"]
            output["stderr"] = dispatch_result["stderr"]
            output["dispatched"] = True
            if dispatch_result["exit_code"] != 0:
                return StepResult(
                    status=StepStatus.FAILED,
                    output=output,
                    error=dispatch_result["stderr"] or f"Command exited with code {dispatch_result['exit_code']}",
                )
            return StepResult(
                status=StepStatus.COMPLETED,
                output=output,
            )
        else:
            output["exit_code"] = 1
            output["dispatched"] = False
            return StepResult(
                status=StepStatus.FAILED,
                output=output,
                error=(
                    f"Cannot dispatch command {command!r}: "
                    f"integration {integration!r} CLI not found or not installed. "
                    f"Install the CLI tool or check 'specify integration list'."
                ),
            )