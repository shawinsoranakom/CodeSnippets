def setUp(self):
        request = self.request_factory.get(reverse("test_adminsite:index"))
        request.user = self.u1
        self.ctx = site.each_context(request)