def __init__(self, request, *args, **kwargs):
        assert isinstance(request, HttpRequest)
        super().__init__(request, *args, **kwargs)