async def astart_index(self):
        """See Page.start_index()."""
        count = await self.paginator.acount()
        if count == 0:
            return 0
        return (self.paginator.per_page * (self.number - 1)) + 1