async def __acall__(self, request):
        """
        Async version of __call__ that is swapped in when an async request
        is running.
        """
        response = None
        if hasattr(self, "process_request"):
            response = await sync_to_async(
                self.process_request,
                thread_sensitive=True,
            )(request)
        response = response or await self.get_response(request)
        if hasattr(self, "process_response"):
            response = await sync_to_async(
                self.process_response,
                thread_sensitive=True,
            )(request, response)
        return response