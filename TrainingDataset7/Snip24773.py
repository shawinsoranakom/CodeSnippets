def __call__(self, request):
        """Return an unawaited coroutine (common error for async views)."""
        # Store coroutine to suppress 'unawaited' warning message
        self._unawaited_coroutine = asyncio.sleep(0)
        return self._unawaited_coroutine