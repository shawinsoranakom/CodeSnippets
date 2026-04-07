async def get_response_async(self, request):
        try:
            return await sync_to_async(self.serve, thread_sensitive=False)(request)
        except Http404 as e:
            return await sync_to_async(response_for_exception, thread_sensitive=False)(
                request, e
            )