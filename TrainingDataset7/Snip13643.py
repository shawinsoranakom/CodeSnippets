def request(self, **request):
        """Construct a generic request object."""
        # This is synchronous, which means all methods on this class are.
        # AsyncClient, however, has an async request function, which makes all
        # its methods async.
        if "_body_file" in request:
            body_file = request.pop("_body_file")
        else:
            body_file = FakePayload("")
        # Wrap FakePayload body_file to allow large read() in test environment.
        return ASGIRequest(
            self._base_scope(**request), LimitedStream(body_file, len(body_file))
        )