async def _step_with_exception_handling(self) -> None:
        try:
            await self._step()
        except Exception as e:
            self.log(
                'error',
                f'Error while running the agent (session ID: {self.id}): {e}',
                exc_info=True,
            )
            reported = RuntimeError(
                f'There was an unexpected error while running the agent: {e.__class__.__name__}. You can refresh the page or ask the agent to try again.'
            )
            if (
                isinstance(e, Timeout)
                or isinstance(e, APIError)
                or isinstance(e, BadRequestError)
                or isinstance(e, NotFoundError)
                or isinstance(e, InternalServerError)
                or isinstance(e, AuthenticationError)
                or isinstance(e, RateLimitError)
                or isinstance(e, ContentPolicyViolationError)
                or isinstance(e, LLMContextWindowExceedError)
            ):
                reported = e
            else:
                self.log(
                    'warning',
                    f'Unknown exception type while running the agent: {type(e).__name__}.',
                )
            await self._react_to_exception(reported)