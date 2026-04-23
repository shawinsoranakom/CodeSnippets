def stopped(self) -> Awaitable[None]:
        """A Future that completes when the Server's run loop has exited."""
        return self._runtime.stopped