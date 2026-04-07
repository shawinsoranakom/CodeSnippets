def check_accept_language_vary(self, accept_language, vary, reference_key):
        request = self.factory.get(self.path)
        request.META["HTTP_ACCEPT_LANGUAGE"] = accept_language
        request.META["HTTP_ACCEPT_ENCODING"] = "gzip;q=1.0, identity; q=0.5, *;q=0"
        response = HttpResponse()
        response.headers["Vary"] = vary
        key = learn_cache_key(request, response)
        key2 = get_cache_key(request)
        self.assertEqual(key, reference_key)
        self.assertEqual(key2, reference_key)