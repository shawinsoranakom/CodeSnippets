def test_binary_not_contains(self):
        r = self.client.get("/check_binary/")
        self.assertNotContains(r, b"%ODF-1.4\r\n%\x93\x8c\x8b\x9e")
        with self.assertRaises(AssertionError):
            self.assertNotContains(r, b"%PDF-1.4\r\n%\x93\x8c\x8b\x9e")