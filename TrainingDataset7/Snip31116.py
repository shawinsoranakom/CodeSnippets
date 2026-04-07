def test_http_get_host(self):
        # Check if X_FORWARDED_HOST is provided.
        request = HttpRequest()
        request.META = {
            "HTTP_X_FORWARDED_HOST": "forward.com",
            "HTTP_HOST": "example.com",
            "SERVER_NAME": "internal.com",
            "SERVER_PORT": 80,
        }
        # X_FORWARDED_HOST is ignored.
        self.assertEqual(request.get_host(), "example.com")

        # Check if X_FORWARDED_HOST isn't provided.
        request = HttpRequest()
        request.META = {
            "HTTP_HOST": "example.com",
            "SERVER_NAME": "internal.com",
            "SERVER_PORT": 80,
        }
        self.assertEqual(request.get_host(), "example.com")

        # Check if HTTP_HOST isn't provided.
        request = HttpRequest()
        request.META = {
            "SERVER_NAME": "internal.com",
            "SERVER_PORT": 80,
        }
        self.assertEqual(request.get_host(), "internal.com")

        # Check if HTTP_HOST isn't provided, and we're on a nonstandard port
        request = HttpRequest()
        request.META = {
            "SERVER_NAME": "internal.com",
            "SERVER_PORT": 8042,
        }
        self.assertEqual(request.get_host(), "internal.com:8042")

        legit_hosts = [
            "example.com",
            "example.com:80",
            "12.34.56.78",
            "12.34.56.78:443",
            "[2001:19f0:feee::dead:beef:cafe]",
            "[2001:19f0:feee::dead:beef:cafe]:8080",
            "xn--4ca9at.com",  # Punycode for öäü.com
            "anything.multitenant.com",
            "multitenant.com",
            "insensitive.com",
            "example.com.",
            "example.com.:80",
            "[::ffff:169.254.169.254]",
        ]

        for host in legit_hosts:
            request = HttpRequest()
            request.META = {
                "HTTP_HOST": host,
            }
            request.get_host()

        # Poisoned host headers are rejected as suspicious
        for host in chain(self.poisoned_hosts, ["other.com", "example.com.."]):
            with self.assertRaises(DisallowedHost):
                request = HttpRequest()
                request.META = {
                    "HTTP_HOST": host,
                }
                request.get_host()