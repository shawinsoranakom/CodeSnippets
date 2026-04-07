def test_binary_contains(self):
        r = self.client.get("/check_binary/")
        self.assertContains(r, b"%PDF-1.4\r\n%\x93\x8c\x8b\x9e")
        with self.assertRaises(AssertionError):
            self.assertContains(r, b"%PDF-1.4\r\n%\x93\x8c\x8b\x9e", count=2)