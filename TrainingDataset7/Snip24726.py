def test_request_signals(self):
        response = self.client.get("/regular/")
        self.assertEqual(self.signals, ["started", "finished"])
        self.assertEqual(response.content, b"regular content")
        self.assertEqual(self.signaled_environ, response.wsgi_request.environ)