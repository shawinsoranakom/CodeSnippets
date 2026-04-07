def test_unicode_not_contains(self):
        """
        Unicode characters can be searched for, and not found in template
        context
        """
        # Regression test for #10183
        r = self.client.get("/check_unicode/")
        self.assertNotContains(r, "はたけ")
        self.assertNotContains(r, b"\xe3\x81\xaf\xe3\x81\x9f\xe3\x81\x91".decode())