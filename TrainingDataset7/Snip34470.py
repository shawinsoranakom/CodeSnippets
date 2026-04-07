def middleware(request):
        request.urlconf = "template_tests.alternate_urls"
        return get_response(request)