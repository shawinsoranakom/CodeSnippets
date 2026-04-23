def test_get_port(self):
        request = HttpRequest()
        request.META = {
            "SERVER_PORT": "8080",
            "HTTP_X_FORWARDED_PORT": "80",
        }
        # Shouldn't use the X-Forwarded-Port header
        self.assertEqual(request.get_port(), "8080")

        request = HttpRequest()
        request.META = {
            "SERVER_PORT": "8080",
        }
        self.assertEqual(request.get_port(), "8080")