def get_response(self, request):
        """Return an HttpResponse object for the given HttpRequest."""
        # Setup default url resolver for this thread
        set_urlconf(settings.ROOT_URLCONF)
        response = self._middleware_chain(request)
        response._resource_closers.append(request.close)
        if response.status_code >= 400:
            log_response(
                "%s: %s",
                response.reason_phrase,
                request.path,
                response=response,
                request=request,
            )
        return response