def __iter__(self):
        try:
            return iter(self.streaming_content)
        except TypeError:
            warnings.warn(
                "StreamingHttpResponse must consume asynchronous iterators in order to "
                "serve them synchronously. Use a synchronous iterator instead.",
                Warning,
                stacklevel=2,
            )

            # async iterator. Consume in async_to_sync and map back.
            async def to_list(_iterator):
                as_list = []
                async for chunk in _iterator:
                    as_list.append(chunk)
                return as_list

            return map(self.make_bytes, iter(async_to_sync(to_list)(self._iterator)))