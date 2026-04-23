async def asave(
        self,
        *,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        return await sync_to_async(self.save)(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )