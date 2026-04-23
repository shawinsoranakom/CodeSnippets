def http_method_not_allowed(self, request, *args, **kwargs):
        response = HttpResponseNotAllowed(self._allowed_methods())
        log_response(
            "Method Not Allowed (%s): %s",
            request.method,
            request.path,
            response=response,
            request=request,
        )

        if self.view_is_async:

            async def func():
                return response

            return func()
        else:
            return response