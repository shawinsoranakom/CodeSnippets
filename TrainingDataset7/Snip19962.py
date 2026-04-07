def setUp(self):
        self.request = HttpRequest()
        self.request.META = {"SERVER_NAME": "Example.com", "SERVER_PORT": "80"}