def test_exception_report_uses_meta_filtering(self):
        response = self.client.get(
            "/raises500/", headers={"secret-header": "super_secret"}
        )
        self.assertNotIn(b"super_secret", response.content)
        response = self.client.get(
            "/raises500/",
            headers={"secret-header": "super_secret", "accept": "application/json"},
        )
        self.assertNotIn(b"super_secret", response.content)