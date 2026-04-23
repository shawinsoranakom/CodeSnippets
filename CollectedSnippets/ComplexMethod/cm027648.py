async def async_run(
        self,
        run_variables: _VarsType | None = None,
        context: Context | None = None,
        started_action: Callable[..., Any] | None = None,
    ) -> ScriptRunResult | None:
        """Run script."""
        if context is None:
            self._log(
                "Running script requires passing in a context", level=logging.WARNING
            )
            context = Context()

        # Prevent spawning new script runs when Home Assistant is shutting down
        if DATA_NEW_SCRIPT_RUNS_NOT_ALLOWED in self._hass.data:
            self._log("Home Assistant is shutting down, starting script blocked")
            return None

        # Prevent spawning new script runs if not allowed by script mode
        if self.is_running:
            if self.script_mode == SCRIPT_MODE_SINGLE:
                if self._max_exceeded != "SILENT":
                    self._log("Already running", level=LOGSEVERITY[self._max_exceeded])
                script_execution_set("failed_single")
                return None
            if self.script_mode != SCRIPT_MODE_RESTART and self.runs == self.max_runs:
                if self._max_exceeded != "SILENT":
                    self._log(
                        "Maximum number of runs exceeded",
                        level=LOGSEVERITY[self._max_exceeded],
                    )
                script_execution_set("failed_max_runs")
                return None

        # If this is a top level Script then make a copy of the variables in case they
        # are read-only, but more importantly, so as not to leak any variables created
        # during the run back to the caller.
        if self.top_level:
            if self.variables:
                try:
                    run_variables = self.variables.async_render(
                        self._hass,
                        run_variables,
                    )
                except exceptions.TemplateError as err:
                    self._log("Error rendering variables: %s", err, level=logging.ERROR)
                    raise

            variables = ScriptRunVariables.create_top_level(run_variables)
            variables["context"] = context
        else:
            # This is not the top level script, run_variables is an instance of ScriptRunVariables
            variables = cast(ScriptRunVariables, run_variables)

        # Prevent non-allowed recursive calls which will cause deadlocks when we try to
        # stop (restart) or wait for (queued) our own script run.
        script_stack = script_stack_cv.get()
        if (
            self.script_mode in (SCRIPT_MODE_RESTART, SCRIPT_MODE_QUEUED)
            and script_stack is not None
            and self.unique_id in script_stack
        ):
            script_execution_set("disallowed_recursion_detected")
            formatted_stack = [
                f"- {name_id.partition('-')[0]}" for name_id in script_stack
            ]
            self._log(
                "Disallowed recursion detected, "
                f"{script_stack[-1].partition('-')[0]} tried to start "
                f"{self.domain}.{self.name} which is already running "
                "in the current execution path; "
                "Traceback (most recent call last):\n"
                f"{'\n'.join(formatted_stack)}",
                level=logging.WARNING,
            )
            return None

        if self.script_mode != SCRIPT_MODE_QUEUED:
            cls = _ScriptRun
        else:
            cls = _QueuedScriptRun
        run = cls(self._hass, self, variables, context, self._log_exceptions)
        has_existing_runs = bool(self._runs)
        self._runs.append(run)
        if self.script_mode == SCRIPT_MODE_RESTART and has_existing_runs:
            # When script mode is SCRIPT_MODE_RESTART, first add the new run and then
            # stop any other runs. If we stop other runs first, self.is_running will
            # return false after the other script runs were stopped until our task
            # resumes running. Its important that we check if there are existing
            # runs before sleeping as otherwise if two runs are started at the exact
            # same time they will cancel each other out.
            self._log("Restarting")
            await self.async_stop(update_state=False, spare=run)

        if started_action:
            started_action()
        self.last_triggered = utcnow()
        self._changed()

        try:
            return await asyncio.shield(create_eager_task(run.async_run()))
        except asyncio.CancelledError:
            await run.async_stop()
            self._changed()
            raise