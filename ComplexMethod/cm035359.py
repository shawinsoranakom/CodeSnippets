async def _react_to_exception(
        self,
        e: Exception,
    ) -> None:
        """React to an exception by setting the agent state to error and sending a status message."""
        # Store the error reason before setting the agent state
        self.state.last_error = f'{type(e).__name__}: {str(e)}'

        if self.status_callback is not None:
            runtime_status = RuntimeStatus.ERROR
            if isinstance(e, AuthenticationError):
                runtime_status = RuntimeStatus.ERROR_LLM_AUTHENTICATION
                self.state.last_error = runtime_status.value
            elif isinstance(
                e,
                (
                    ServiceUnavailableError,
                    APIConnectionError,
                    APIError,
                ),
            ):
                runtime_status = RuntimeStatus.ERROR_LLM_SERVICE_UNAVAILABLE
                self.state.last_error = runtime_status.value
            elif isinstance(e, InternalServerError):
                runtime_status = RuntimeStatus.ERROR_LLM_INTERNAL_SERVER_ERROR
                self.state.last_error = runtime_status.value
            elif isinstance(e, BadRequestError) and 'ExceededBudget' in str(e):
                runtime_status = RuntimeStatus.ERROR_LLM_OUT_OF_CREDITS
                self.state.last_error = runtime_status.value
            elif isinstance(e, ContentPolicyViolationError) or (
                isinstance(e, BadRequestError)
                and 'ContentPolicyViolationError' in str(e)
            ):
                runtime_status = RuntimeStatus.ERROR_LLM_CONTENT_POLICY_VIOLATION
                self.state.last_error = runtime_status.value
            elif isinstance(e, RateLimitError):
                # Check if this is the final retry attempt
                if (
                    hasattr(e, 'retry_attempt')
                    and hasattr(e, 'max_retries')
                    and e.retry_attempt >= e.max_retries
                ):
                    # All retries exhausted, set to ERROR state with a special message
                    self.state.last_error = (
                        RuntimeStatus.AGENT_RATE_LIMITED_STOPPED_MESSAGE.value
                    )
                    await self.set_agent_state_to(AgentState.ERROR)
                else:
                    # Still retrying, set to RATE_LIMITED state
                    await self.set_agent_state_to(AgentState.RATE_LIMITED)
                return
            self.status_callback('error', runtime_status, self.state.last_error)

        # Set the agent state to ERROR after storing the reason
        await self.set_agent_state_to(AgentState.ERROR)