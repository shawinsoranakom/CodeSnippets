def test_build_absolute_uri(self):
        factory = RequestFactory()
        request = factory.get("/")
        self.assertEqual(
            request.build_absolute_uri(reverse_lazy("some-login-page")),
            "http://testserver/login/",
        )