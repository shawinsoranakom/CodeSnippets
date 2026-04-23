def _eval_body(self, env: Environment) -> None:
        try:
            while env.is_running():
                next_state: CommonStateField = self._get_state(env.next_state_name)
                next_state.eval(env)
                # Garbage collect hanging values added by this last state.
                env.stack.clear()
                env.heap.clear()
        except FailureEventException as ex:
            env.set_error(error=ex.get_execution_failed_event_details())
        except Exception as ex:
            cause = f"{type(ex).__name__}({str(ex)})"
            LOG.error("Stepfunctions computation ended with exception '%s'.", cause)
            env.set_error(
                ExecutionFailedEventDetails(
                    error=StatesErrorName(typ=StatesErrorNameType.StatesRuntime).error_name,
                    cause=cause,
                )
            )

        # If the program is evaluating within a frames then these are not allowed to produce program termination states.
        if env.is_frame():
            return

        program_state: ProgramState = env.program_state()
        if isinstance(program_state, ProgramError):
            exec_failed_event_details = select_from_typed_dict(
                typed_dict=ExecutionFailedEventDetails, obj=program_state.error or {}
            )
            env.event_manager.add_event(
                context=env.event_history_context,
                event_type=HistoryEventType.ExecutionFailed,
                event_details=EventDetails(executionFailedEventDetails=exec_failed_event_details),
            )
        elif isinstance(program_state, ProgramStopped):
            env.event_history_context.source_event_id = 0
            env.event_manager.add_event(
                context=env.event_history_context,
                event_type=HistoryEventType.ExecutionAborted,
                event_details=EventDetails(
                    executionAbortedEventDetails=ExecutionAbortedEventDetails(
                        error=program_state.error, cause=program_state.cause
                    )
                ),
            )
        elif isinstance(program_state, ProgramTimedOut):
            env.event_manager.add_event(
                context=env.event_history_context,
                event_type=HistoryEventType.ExecutionTimedOut,
                event_details=EventDetails(
                    executionTimedOutEventDetails=ExecutionTimedOutEventDetails()
                ),
            )
        elif isinstance(program_state, ProgramEnded):
            env.event_manager.add_event(
                context=env.event_history_context,
                event_type=HistoryEventType.ExecutionSucceeded,
                event_details=EventDetails(
                    executionSucceededEventDetails=ExecutionSucceededEventDetails(
                        output=to_json_str(env.states.get_input(), separators=(",", ":")),
                        outputDetails=HistoryEventExecutionDataDetails(
                            truncated=False  # Always False for api calls.
                        ),
                    )
                ),
            )