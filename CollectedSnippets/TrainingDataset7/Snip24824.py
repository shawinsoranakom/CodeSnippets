def test_not_modified(self):
        response = HttpResponseNotModified()
        self.assertEqual(response.status_code, 304)
        # 304 responses should not have content/content-type
        with self.assertRaises(AttributeError):
            response.content = "Hello dear"
        self.assertNotIn("content-type", response)