def test_unicode_contains(self):
        "Unicode characters can be found in template context"
        # Regression test for #10183
        r = self.client.get("/check_unicode/")
        self.assertContains(r, "さかき")
        self.assertContains(r, b"\xe5\xb3\xa0".decode())