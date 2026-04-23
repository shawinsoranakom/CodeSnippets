async def __call__(self, messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> StopMessage | None:
        if self.terminated:
            raise TerminatedException("Termination condition has already been reached.")
        # Check all remaining conditions.
        stop_messages = await asyncio.gather(
            *[condition(messages) for condition in self._conditions if not condition.terminated]
        )
        # Collect stop messages.
        for stop_message in stop_messages:
            if stop_message is not None:
                self._stop_messages.append(stop_message)
        if any(stop_message is None for stop_message in stop_messages):
            # If any remaining condition has not reached termination, it is not terminated.
            return None
        content = ", ".join(stop_message.content for stop_message in self._stop_messages)
        source = ", ".join(stop_message.source for stop_message in self._stop_messages)
        return StopMessage(content=content, source=source)