async def arefresh_from_db(self, using=None, fields=None, from_queryset=None):
        return await sync_to_async(self.refresh_from_db)(
            using=using, fields=fields, from_queryset=from_queryset
        )