def async_middleware_urlconf(get_response):
    async def middleware(request):
        request.urlconf = "test_client.urls_middleware_urlconf"
        return await get_response(request)

    return middleware