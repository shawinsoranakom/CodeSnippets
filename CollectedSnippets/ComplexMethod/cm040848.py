def _eval_tolerated_failure_percentage(self, env: Environment) -> float:
        self.string_sampler.eval(env=env)
        tolerated_failure_percentage = env.stack.pop()

        if isinstance(tolerated_failure_percentage, str):
            try:
                tolerated_failure_percentage = int(tolerated_failure_percentage)
            except Exception:
                # Pass the invalid type forward for validation error
                pass

        if isinstance(tolerated_failure_percentage, int):
            tolerated_failure_percentage = float(tolerated_failure_percentage)

        error_cause = None
        if not isinstance(tolerated_failure_percentage, float):
            value_str = (
                to_json_str(tolerated_failure_percentage)
                if not isinstance(tolerated_failure_percentage, str)
                else tolerated_failure_percentage
            )
            error_cause = (
                f'The ToleratedFailurePercentagePath field refers to value "{value_str}" '
                f"which is not a valid float: {self.string_sampler.literal_value}"
            )
        elif (
            not TOLERATED_FAILURE_PERCENTAGE_MIN
            <= tolerated_failure_percentage
            <= TOLERATED_FAILURE_PERCENTAGE_MAX
        ):
            error_cause = "ToleratedFailurePercentage must be between 0 and 100."

        if error_cause is not None:
            raise FailureEventException(
                failure_event=FailureEvent(
                    env=env,
                    error_name=StatesErrorName(typ=StatesErrorNameType.StatesRuntime),
                    event_type=HistoryEventType.ExecutionFailed,
                    event_details=EventDetails(
                        executionFailedEventDetails=ExecutionFailedEventDetails(
                            error=StatesErrorNameType.StatesRuntime.to_name(), cause=error_cause
                        )
                    ),
                )
            )

        return tolerated_failure_percentage