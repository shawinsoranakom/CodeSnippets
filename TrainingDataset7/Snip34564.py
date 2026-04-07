async def middleware(request):
        request.urlconf = "test_client.urls_middleware_urlconf"
        return await get_response(request)