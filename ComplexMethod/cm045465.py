async def __call__(self, messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> StopMessage | None:
        if self.terminated:
            raise RuntimeError("Termination condition has already been reached")
        stop_messages = await asyncio.gather(*[condition(messages) for condition in self._conditions])
        stop_messages_filter = [stop_message for stop_message in stop_messages if stop_message is not None]
        if len(stop_messages_filter) > 0:
            content = ", ".join(stop_message.content for stop_message in stop_messages_filter)
            source = ", ".join(stop_message.source for stop_message in stop_messages_filter)
            return StopMessage(content=content, source=source)
        return None