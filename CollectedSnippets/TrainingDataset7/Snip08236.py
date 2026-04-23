async def adecr_version(self, key, delta=1, version=None):
        return await self.aincr_version(key, -delta, version)