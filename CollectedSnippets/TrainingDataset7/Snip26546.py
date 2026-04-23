def process_response(self, *args, secure=False, request=None, **kwargs):
        request_kwargs = {}
        if secure:
            request_kwargs.update(self.secure_request_kwargs)
        if request is None:
            request = self.request.get("/some/url", **request_kwargs)
        ret = self.middleware(*args, **kwargs).process_request(request)
        if ret:
            return ret
        return self.middleware(*args, **kwargs)(request)