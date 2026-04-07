def streaming_content(self):
        if self.is_async:
            # pull to lexical scope to capture fixed reference in case
            # streaming_content is set again later.
            _iterator = self._iterator

            async def awrapper():
                async for part in _iterator:
                    yield self.make_bytes(part)

            return awrapper()
        else:
            return map(self.make_bytes, self._iterator)