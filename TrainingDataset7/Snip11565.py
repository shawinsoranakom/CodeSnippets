async def aset(self, objs, *, clear=False, through_defaults=None):
            return await sync_to_async(self.set)(
                objs=objs, clear=clear, through_defaults=through_defaults
            )