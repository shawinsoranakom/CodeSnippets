def test_response_redirect_class_subclass(self):
        class MyCommonMiddleware(CommonMiddleware):
            response_redirect_class = HttpResponseRedirect

        request = self.rf.get("/slash")
        r = MyCommonMiddleware(get_response_404)(request)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, "/slash/")
        self.assertIsInstance(r, HttpResponseRedirect)