async def aget_by_natural_key(self, username):
        return await self.aget(**{self.model.USERNAME_FIELD: username})