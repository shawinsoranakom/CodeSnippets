def setUp(self):
        self.request = HttpRequest()
        self.request.session = self.client.session