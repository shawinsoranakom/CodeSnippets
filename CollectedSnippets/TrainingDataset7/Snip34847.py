def test_cookies(self):
        factory = RequestFactory()
        factory.cookies.load('A="B"; C="D"; Path=/; Version=1')
        request = factory.get("/")
        self.assertEqual(request.META["HTTP_COOKIE"], 'A="B"; C="D"')