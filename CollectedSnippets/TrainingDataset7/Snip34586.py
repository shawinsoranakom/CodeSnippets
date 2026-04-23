def test_raw_post(self):
        "POST raw data (with a content type) to a view"
        test_doc = """<?xml version="1.0" encoding="utf-8"?>
        <library><book><title>Blink</title><author>Malcolm Gladwell</author></book>
        </library>
        """
        response = self.client.post(
            "/raw_post_view/", test_doc, content_type="text/xml"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "Book template")
        self.assertEqual(response.content, b"Blink - Malcolm Gladwell")