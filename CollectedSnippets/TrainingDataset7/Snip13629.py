def request(self, **request):
        "Construct a generic request object."
        return WSGIRequest(self._base_environ(**request))