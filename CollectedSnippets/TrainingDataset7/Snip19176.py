def test_location_multiple_servers(self):
        locations = [
            ["server1.tld", "server2:11211"],
            "server1.tld;server2:11211",
            "server1.tld,server2:11211",
        ]
        for location in locations:
            with self.subTest(location=location):
                params = {"BACKEND": self.base_params["BACKEND"], "LOCATION": location}
                with self.settings(CACHES={"default": params}):
                    self.assertEqual(cache._servers, ["server1.tld", "server2:11211"])