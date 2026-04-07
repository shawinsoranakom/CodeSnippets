def test_redirect_to_object(self):
        # We don't really need a model; just something with a get_absolute_url
        class FakeObj:
            def get_absolute_url(self):
                return "/hi-there/"

        res = redirect(FakeObj())
        self.assertIsInstance(res, HttpResponseRedirect)
        self.assertEqual(res.url, "/hi-there/")

        res = redirect(FakeObj(), permanent=True)
        self.assertIsInstance(res, HttpResponsePermanentRedirect)
        self.assertEqual(res.url, "/hi-there/")