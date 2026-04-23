def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        prompt_template = config.get("prompt", "")
        prompt = evaluate_expression(prompt_template, context)
        if not isinstance(prompt, str):
            prompt = str(prompt)

        # Resolve integration (step → workflow default)
        integration = config.get("integration") or context.default_integration
        if integration and isinstance(integration, str) and "{{" in integration:
            integration = evaluate_expression(integration, context)

        # Resolve model
        model = config.get("model") or context.default_model
        if model and isinstance(model, str) and "{{" in model:
            model = evaluate_expression(model, context)

        # Attempt CLI dispatch
        dispatch_result = self._try_dispatch(
            prompt, integration, model, context
        )

        output: dict[str, Any] = {
            "prompt": prompt,
            "integration": integration,
            "model": model,
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
                    error=(
                        dispatch_result["stderr"]
                        or f"Prompt exited with code {dispatch_result['exit_code']}"
                    ),
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
                    f"Cannot dispatch prompt: "
                    f"integration {integration!r} "
                    f"CLI not found or not installed."
                ),
            )