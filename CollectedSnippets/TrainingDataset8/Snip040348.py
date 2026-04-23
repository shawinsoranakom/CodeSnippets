def test_is_url_from_allowed_origins_allowed_domains(self):
        self.assertTrue(server_util.is_url_from_allowed_origins("localhost"))
        self.assertTrue(server_util.is_url_from_allowed_origins("127.0.0.1"))