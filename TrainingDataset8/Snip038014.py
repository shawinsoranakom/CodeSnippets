def stopped(self) -> Awaitable[None]:
        """A Future that completes when the Runtime's run loop has exited."""
        return self._get_async_objs().stopped