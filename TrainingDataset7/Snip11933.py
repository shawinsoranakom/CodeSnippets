def __aiter__(self):
        # Remember, __aiter__ itself is synchronous, it's the thing it returns
        # that is async!
        async def generator():
            await sync_to_async(self._fetch_all)()
            for item in self._result_cache:
                yield item

        return generator()