async def __aenter__(self) -> _T:
        return self._cm.__enter__()