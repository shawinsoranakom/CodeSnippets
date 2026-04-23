async def aupdate(self, dict_):
        (await self._aget_session()).update(dict_)
        self.modified = True