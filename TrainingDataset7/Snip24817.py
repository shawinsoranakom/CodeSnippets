def test_text_updates_when_content_updates(self):
        response = HttpResponse("Hello, world!")
        self.assertEqual(response.text, "Hello, world!")
        response.content = "Updated content"
        self.assertEqual(response.text, "Updated content")