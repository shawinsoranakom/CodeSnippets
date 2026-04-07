async def awrapper():
                async for part in _iterator:
                    yield self.make_bytes(part)