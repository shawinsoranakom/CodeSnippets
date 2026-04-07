def test_add_empty(self):
        media = Media(css={"screen": ["a.css"]}, js=["a"])
        empty_media = Media()
        merged = media + empty_media
        self.assertEqual(merged._css_lists, [{"screen": ["a.css"]}])
        self.assertEqual(merged._js_lists, [["a"]])