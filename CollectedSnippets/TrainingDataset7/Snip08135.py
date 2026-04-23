async def awrapper():
                for part in await sync_to_async(list)(_iterator):
                    yield part