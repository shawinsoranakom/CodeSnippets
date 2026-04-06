async def __aexit__(self, *exc_info: object) -> None:
        await self._router._shutdown()