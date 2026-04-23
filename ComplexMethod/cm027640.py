async def async_run(self) -> ScriptRunResult | None:
        """Run script."""
        self._started = True
        # Push the script to the script execution stack
        if (script_stack := script_stack_cv.get()) is None:
            script_stack = []
            script_stack_cv.set(script_stack)
        script_stack.append(self._script.unique_id)
        response = None

        try:
            self._log("Running %s", self._script.running_description)
            for self._step, self._action in enumerate(self._script.sequence):
                if self._stop.done():
                    script_execution_set("cancelled")
                    break
                await self._async_step(log_exceptions=False)
            else:
                script_execution_set("finished")
        except _AbortScript:
            script_execution_set("aborted")
            # Let the _AbortScript bubble up if this is a sub-script
            if not self._script.top_level:
                raise
        except _ConditionFail:
            script_execution_set("aborted")
        except _StopScript as err:
            script_execution_set("finished", err.response)

            # Let the _StopScript bubble up if this is a sub-script
            if not self._script.top_level:
                raise

            response = err.response

        except Exception:
            script_execution_set("error")
            raise
        finally:
            # Pop the script from the script execution stack
            script_stack.pop()
            self._finish()

        return ScriptRunResult(
            self._conversation_response, response, self._variables.local_scope
        )