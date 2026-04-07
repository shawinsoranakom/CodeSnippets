def assertBackendInSession(self, backend):
        request = HttpRequest()
        request.session = self.client.session
        self.assertEqual(request.session[BACKEND_SESSION_KEY], backend)