async def aget_result(self, result_id):
        """See get_result()."""
        return await sync_to_async(self.get_result, thread_sensitive=True)(
            result_id=result_id
        )