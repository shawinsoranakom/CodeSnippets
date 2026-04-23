def _execute_steps(
        self,
        steps: list[dict[str, Any]],
        context: StepContext,
        state: RunState,
        registry: dict[str, Any],
        *,
        step_offset: int = 0,
    ) -> None:
        """Execute a list of steps sequentially."""
        for i, step_config in enumerate(steps):
            step_id = step_config.get("id", f"step-{i}")
            step_type = step_config.get("type", "command")

            state.current_step_id = step_id
            if step_offset >= 0:
                state.current_step_index = step_offset + i
            state.save()

            state.append_log(
                {"event": "step_started", "step_id": step_id, "type": step_type}
            )

            # Log progress — use the engine's on_step_start callback if set,
            # otherwise stay silent (library-safe default).
            label = step_config.get("command", "") or step_type
            if self.on_step_start is not None:
                self.on_step_start(step_id, label)

            step_impl = registry.get(step_type)
            if not step_impl:
                state.status = RunStatus.FAILED
                state.append_log(
                    {
                        "event": "step_failed",
                        "step_id": step_id,
                        "error": f"Unknown step type: {step_type!r}",
                    }
                )
                state.save()
                return

            result: StepResult = step_impl.execute(step_config, context)

            # Record step results — prefer resolved values from step output
            step_data = {
                "integration": result.output.get("integration")
                or step_config.get("integration")
                or context.default_integration,
                "model": result.output.get("model")
                or step_config.get("model")
                or context.default_model,
                "options": result.output.get("options")
                or step_config.get("options", {}),
                "input": result.output.get("input")
                or step_config.get("input", {}),
                "output": result.output,
                "status": result.status.value,
            }
            context.steps[step_id] = step_data
            state.step_results[step_id] = step_data

            state.append_log(
                {
                    "event": "step_completed",
                    "step_id": step_id,
                    "status": result.status.value,
                }
            )

            # Handle gate pauses
            if result.status == StepStatus.PAUSED:
                state.status = RunStatus.PAUSED
                state.save()
                return

            # Handle failures
            if result.status == StepStatus.FAILED:
                # Gate abort (output.aborted) maps to ABORTED status
                if result.output.get("aborted"):
                    state.status = RunStatus.ABORTED
                    state.append_log(
                        {
                            "event": "workflow_aborted",
                            "step_id": step_id,
                        }
                    )
                else:
                    state.status = RunStatus.FAILED
                    state.append_log(
                        {
                            "event": "step_failed",
                            "step_id": step_id,
                            "error": result.error,
                        }
                    )
                state.save()
                return

            # Execute nested steps (from control flow)
            # NOTE: Nested steps run with step_offset=-1 so they don't
            # update current_step_index.  If a nested step pauses,
            # resume will re-run the parent step and its nested body.
            # A step-path stack for exact nested resume is a future
            # enhancement.
            if result.next_steps:
                self._execute_steps(
                    result.next_steps, context, state, registry,
                    step_offset=-1,
                )
                if state.status in (
                    RunStatus.PAUSED,
                    RunStatus.FAILED,
                    RunStatus.ABORTED,
                ):
                    return

                # Loop iteration: while/do-while re-evaluate after body
                if step_type in ("while", "do-while"):
                    from .expressions import evaluate_condition

                    max_iters = step_config.get("max_iterations")
                    if not isinstance(max_iters, int) or max_iters < 1:
                        max_iters = 10
                    condition = step_config.get("condition", False)
                    for _loop_iter in range(max_iters - 1):
                        if not evaluate_condition(condition, context):
                            break
                        # Namespace nested step IDs per iteration
                        iter_steps = []
                        for ns in result.next_steps:
                            ns_copy = dict(ns)
                            if "id" in ns_copy:
                                ns_copy["id"] = f"{step_id}:{ns_copy['id']}:{_loop_iter + 1}"
                            iter_steps.append(ns_copy)
                        self._execute_steps(
                            iter_steps, context, state, registry,
                            step_offset=-1,
                        )
                        if state.status in (
                            RunStatus.PAUSED,
                            RunStatus.FAILED,
                            RunStatus.ABORTED,
                        ):
                            return

            # Fan-out: execute nested step template per item with unique IDs
            if step_type == "fan-out":
                items = result.output.get("items", [])
                template = result.output.get("step_template", {})
                if template and items:
                    fan_out_results = []
                    for item_idx, item_val in enumerate(result.output["items"]):
                        context.item = item_val
                        # Per-item ID: parentId:templateId:index
                        item_step = dict(template)
                        base_id = item_step.get("id", "item")
                        item_step["id"] = f"{step_id}:{base_id}:{item_idx}"
                        self._execute_steps(
                            [item_step], context, state, registry,
                            step_offset=-1,
                        )
                        # Collect per-item result for fan-in
                        item_result = context.steps.get(item_step["id"], {})
                        fan_out_results.append(item_result.get("output", {}))
                        if state.status in (
                            RunStatus.PAUSED,
                            RunStatus.FAILED,
                            RunStatus.ABORTED,
                        ):
                            break
                    context.item = None
                    # Preserve original output and add collected results
                    fan_out_output = dict(result.output)
                    fan_out_output["results"] = fan_out_results
                    context.steps[step_id]["output"] = fan_out_output
                    state.step_results[step_id]["output"] = fan_out_output
                    if state.status in (
                        RunStatus.PAUSED,
                        RunStatus.FAILED,
                        RunStatus.ABORTED,
                    ):
                        return
                else:
                    # Empty items or no template — normalize output
                    result.output["results"] = []
                    context.steps[step_id]["output"] = result.output
                    state.step_results[step_id]["output"] = result.output