def test_httprequest(self):
        request = HttpRequest()
        self.assertEqual(list(request.GET), [])
        self.assertEqual(list(request.POST), [])
        self.assertEqual(list(request.COOKIES), [])
        self.assertEqual(list(request.META), [])

        # .GET and .POST should be QueryDicts
        self.assertEqual(request.GET.urlencode(), "")
        self.assertEqual(request.POST.urlencode(), "")

        # and FILES should be MultiValueDict
        self.assertEqual(request.FILES.getlist("foo"), [])

        self.assertIsNone(request.content_type)
        self.assertIsNone(request.content_params)