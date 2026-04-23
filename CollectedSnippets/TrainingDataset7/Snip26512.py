def __init__(self):
        request = RequestFactory().get("/")
        request._messages = DummyStorage()
        self.wsgi_request = request