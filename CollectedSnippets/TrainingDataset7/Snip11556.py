async def aadd(self, *objs, through_defaults=None):
            return await sync_to_async(self.add)(
                *objs, through_defaults=through_defaults
            )