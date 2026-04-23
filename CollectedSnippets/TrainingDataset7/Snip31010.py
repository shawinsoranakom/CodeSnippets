def test_empty(self):
        for empty_media_type in (None, "", "  "):
            with self.subTest(media_type=empty_media_type):
                media_type = MediaType(empty_media_type)
                self.assertEqual(str(media_type), "")
                self.assertEqual(repr(media_type), "<MediaType: >")