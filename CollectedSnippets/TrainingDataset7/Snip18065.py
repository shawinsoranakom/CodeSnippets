def setUp(self):
        self.middleware = AuthenticationMiddleware(lambda req: HttpResponse())
        self.client.force_login(self.user)
        self.request = HttpRequest()
        self.request.session = self.client.session
        # Populate self.request.user.
        self.middleware(self.request)
        # .user is lazy, so materialize it by accessing an attribute.
        self.request.user.is_authenticated