async def apop(self, key, default=__not_given):
        self.modified = self.modified or key in (await self._aget_session())
        args = () if default is self.__not_given else (default,)
        return (await self._aget_session()).pop(key, *args)