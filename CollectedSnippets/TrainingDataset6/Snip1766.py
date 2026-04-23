async def __aenter__(self) -> None:
        await self._router._startup()