def test_get_port_with_x_forwarded_port(self):
        request = HttpRequest()
        request.META = {
            "SERVER_PORT": "8080",
            "HTTP_X_FORWARDED_PORT": "80",
        }
        # Should use the X-Forwarded-Port header
        self.assertEqual(request.get_port(), "80")

        request = HttpRequest()
        request.META = {
            "SERVER_PORT": "8080",
        }
        self.assertEqual(request.get_port(), "8080")