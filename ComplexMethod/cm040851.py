def _eval_state(self, env: Environment) -> None:
        # Initialise the retry counter for execution states.
        env.states.context_object.context_object_data["State"]["RetryCount"] = 0

        # Attempt to evaluate the state's logic through until it's successful, caught, or retries have run out.
        while env.is_running():
            try:
                self._evaluate_with_timeout(env)
                break
            except Exception as ex:
                failure_event: FailureEvent = self._from_error(env=env, ex=ex)
                error_output = self._construct_error_output_value(failure_event=failure_event)
                env.states.set_error_output(error_output)

                if self.retry:
                    retry_outcome: RetryOutcome = self._handle_retry(
                        env=env, failure_event=failure_event
                    )
                    if retry_outcome == RetryOutcome.CanRetry:
                        continue

                if failure_event.event_type != HistoryEventType.ExecutionFailed:
                    if (
                        isinstance(ex, FailureEventException)
                        and failure_event.event_type == HistoryEventType.EvaluationFailed
                    ):
                        env.event_manager.add_event(
                            context=env.event_history_context,
                            event_type=HistoryEventType.EvaluationFailed,
                            event_details=EventDetails(
                                evaluationFailedEventDetails=ex.get_evaluation_failed_event_details(),
                            ),
                        )
                    env.event_manager.add_event(
                        context=env.event_history_context,
                        event_type=HistoryEventType.MapStateFailed,
                    )

                if self.catch:
                    self._handle_catch(env=env, failure_event=failure_event)
                    catch_outcome: CatchOutcome = env.stack[-1]
                    if catch_outcome == CatchOutcome.Caught:
                        break

                self._handle_uncaught(env=env, failure_event=failure_event)