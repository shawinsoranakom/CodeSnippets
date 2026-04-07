def response(self, *args, headers=None, **kwargs):
        def get_response(req):
            response = HttpResponse(*args, **kwargs)
            if headers:
                for k, v in headers.items():
                    response.headers[k] = v
            return response

        return get_response