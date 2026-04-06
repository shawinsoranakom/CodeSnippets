async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async with AsyncExitStack() as stack:
            scope[self.context_name] = stack
            await self.app(scope, receive, send)