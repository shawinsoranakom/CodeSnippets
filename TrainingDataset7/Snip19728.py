def assertNotModified(self, response):
        self.assertEqual(response.status_code, 304)
        self.assertEqual(response.content, b"")