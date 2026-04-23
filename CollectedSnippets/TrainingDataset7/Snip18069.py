def setUp(self):
        self.middleware = LoginRequiredMiddleware(lambda req: HttpResponse())
        self.request = HttpRequest()