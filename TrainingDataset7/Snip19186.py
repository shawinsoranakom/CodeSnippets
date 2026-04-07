def test_pylibmc_client_servers(self):
        backend = self.base_params["BACKEND"]
        tests = [
            ("unix:/run/memcached/socket", "/run/memcached/socket"),
            ("/run/memcached/socket", "/run/memcached/socket"),
            ("localhost", "localhost"),
            ("localhost:11211", "localhost:11211"),
            ("[::1]", "[::1]"),
            ("[::1]:11211", "[::1]:11211"),
            ("127.0.0.1", "127.0.0.1"),
            ("127.0.0.1:11211", "127.0.0.1:11211"),
        ]
        for location, expected in tests:
            settings = {"default": {"BACKEND": backend, "LOCATION": location}}
            with self.subTest(location), self.settings(CACHES=settings):
                self.assertEqual(cache.client_servers, [expected])