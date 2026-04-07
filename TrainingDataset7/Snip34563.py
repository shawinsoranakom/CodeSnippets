def middleware(request):
        request.urlconf = "test_client.urls_middleware_urlconf"
        return get_response(request)