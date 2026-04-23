async def aget_result(self, result_id):
        """See get_result()."""
        result = await self.get_backend().aget_result(result_id)
        if result.task.func != self.func:
            raise TaskResultMismatch(
                f"Task does not match (received {result.task.module_path!r})"
            )
        return result