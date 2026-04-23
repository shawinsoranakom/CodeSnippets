async def _step(self) -> None:
        """Executes a single step of the parent or delegate agent. Detects stuck agents and limits on the number of iterations and the task budget."""
        if self.get_agent_state() != AgentState.RUNNING:
            self.log(
                'debug',
                f'Agent not stepping because state is {self.get_agent_state()} (not RUNNING)',
                extra={'msg_type': 'STEP_BLOCKED_STATE'},
            )
            return

        if self._pending_action:
            action_id = getattr(self._pending_action, 'id', 'unknown')
            action_type = type(self._pending_action).__name__
            self.log(
                'debug',
                f'Agent not stepping because of pending action: {action_type} (id={action_id})',
                extra={'msg_type': 'STEP_BLOCKED_PENDING_ACTION'},
            )
            return

        self.log(
            'debug',
            f'LEVEL {self.state.delegate_level} LOCAL STEP {self.state.get_local_step()} GLOBAL STEP {self.state.iteration_flag.current_value}',
            extra={'msg_type': 'STEP'},
        )

        # Synchronize spend across all llm services with the budget flag
        self.state_tracker.sync_budget_flag_with_metrics()
        if self.agent.config.enable_stuck_detection and self._is_stuck():
            await self._react_to_exception(
                AgentStuckInLoopError('Agent got stuck in a loop')
            )
            return

        try:
            self.state_tracker.run_control_flags()
        except Exception as e:
            logger.warning('Control flag limits hit')
            await self._react_to_exception(e)
            return

        action: Action = NullAction()

        if self._replay_manager.should_replay():
            # in replay mode, we don't let the agent to proceed
            # instead, we replay the action from the replay trajectory
            action = self._replay_manager.step()
        else:
            try:
                action = self.agent.step(self.state)
                if action is None:
                    raise LLMNoActionError('No action was returned')
                action._source = EventSource.AGENT  # type: ignore [attr-defined]
            except (
                LLMMalformedActionError,
                LLMNoActionError,
                LLMResponseError,
                FunctionCallValidationError,
                FunctionCallNotExistsError,
            ) as e:
                self.event_stream.add_event(
                    ErrorObservation(
                        content=str(e),
                    ),
                    EventSource.AGENT,
                )
                return
            except (ContextWindowExceededError, BadRequestError, OpenAIError) as e:
                # FIXME: this is a hack until a litellm fix is confirmed
                # Check if this is a nested context window error
                # We have to rely on string-matching because LiteLLM doesn't consistently
                # wrap the failure in a ContextWindowExceededError
                error_str = str(e).lower()
                if (
                    'contextwindowexceedederror' in error_str
                    or 'prompt is too long' in error_str
                    or 'input length and `max_tokens` exceed context limit' in error_str
                    or 'please reduce the length of' in error_str
                    or 'the request exceeds the available context size' in error_str
                    or 'context length exceeded' in error_str
                    # For OpenRouter context window errors
                    or (
                        'sambanovaexception' in error_str
                        and 'maximum context length' in error_str
                    )
                    # For SambaNova context window errors - only match when both patterns are present
                    or isinstance(e, ContextWindowExceededError)
                ):
                    if self.agent.config.enable_history_truncation:
                        self.event_stream.add_event(
                            CondensationRequestAction(), EventSource.AGENT
                        )
                        return
                    else:
                        raise LLMContextWindowExceedError()
                # Check if this is a tool call validation error that should be recoverable
                elif (
                    isinstance(e, BadRequestError)
                    and 'tool call validation failed' in error_str
                    and (
                        'missing properties' in error_str
                        or 'missing required' in error_str
                    )
                ):
                    # Handle tool call validation errors from Groq as recoverable errors
                    self.event_stream.add_event(
                        ErrorObservation(
                            content=f'Tool call validation failed: {str(e)}. Please check the tool parameters and try again.',
                        ),
                        EventSource.AGENT,
                    )
                    return
                else:
                    raise e

        if action.runnable:
            if self.state.confirmation_mode and (
                type(action) is CmdRunAction
                or type(action) is IPythonRunCellAction
                or type(action) is BrowseInteractiveAction
                or type(action) is BrowseURLAction
                or type(action) is FileEditAction
                or type(action) is FileReadAction
                or type(action) is FileWriteAction
                or type(action) is MCPAction
            ):
                # Check if the action has a security_risk attribute set by the LLM or security analyzer
                security_risk = getattr(
                    action, 'security_risk', ActionSecurityRisk.UNKNOWN
                )

                is_high_security_risk = security_risk == ActionSecurityRisk.HIGH
                is_ask_for_every_action = security_risk == ActionSecurityRisk.UNKNOWN

                # If security_risk is HIGH, requires confirmation
                # UNLESS it is CLI which will handle action risks it itself
                if self.agent.config.cli_mode:
                    # TODO(refactor): this is not ideal to have CLI been an exception
                    # We should refactor agent controller to consider this in the future
                    # See issue: https://github.com/OpenHands/OpenHands/issues/10464
                    action.confirmation_state = (  # type: ignore[union-attr]
                        ActionConfirmationStatus.AWAITING_CONFIRMATION
                    )
                # Only HIGH security risk actions require confirmation
                elif (
                    is_high_security_risk or is_ask_for_every_action
                ) and self.confirmation_mode:
                    logger.debug(
                        f'[non-CLI mode] Detected HIGH security risk in action: {action}. Ask for confirmation'
                    )
                    action.confirmation_state = (  # type: ignore[union-attr]
                        ActionConfirmationStatus.AWAITING_CONFIRMATION
                    )
            self._pending_action = action

        if not isinstance(action, NullAction):
            if (
                hasattr(action, 'confirmation_state')
                and action.confirmation_state
                == ActionConfirmationStatus.AWAITING_CONFIRMATION
            ):
                await self.set_agent_state_to(AgentState.AWAITING_USER_CONFIRMATION)

            # Create and log metrics for frontend display
            self._prepare_metrics_for_frontend(action)

            self.event_stream.add_event(action, action._source)  # type: ignore [attr-defined]

        log_level = 'info' if LOG_ALL_EVENTS else 'debug'
        self.log(log_level, str(action), extra={'msg_type': 'ACTION'})