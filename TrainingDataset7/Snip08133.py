async def __call__(self, scope, receive, send):
        # Only even look at HTTP requests
        if scope["type"] == "http" and self._should_handle(scope["path"]):
            # Serve static content
            # (the one thing super() doesn't do is __call__, apparently)
            return await super().__call__(scope, receive, send)
        # Hand off to the main app
        return await self.application(scope, receive, send)