async def get_response_async(self, request):
        response = await super().get_response_async(request)
        response._resource_closers.append(request.close)
        # FileResponse is not async compatible.
        if response.streaming and not response.is_async:
            _iterator = response.streaming_content

            async def awrapper():
                for part in await sync_to_async(list)(_iterator):
                    yield part

            response.streaming_content = awrapper()
        return response