async def adecr(self, key, delta=1, version=None):
        return await self.aincr(key, -delta, version=version)