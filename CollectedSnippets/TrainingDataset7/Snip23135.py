def test_add_css_deduplication(self):
        widget1 = Media(css={"screen": ["a.css"], "all": ["b.css"]})
        widget2 = Media(css={"screen": ["c.css"]})
        widget3 = Media(css={"screen": ["a.css"], "all": ["b.css", "c.css"]})
        widget4 = Media(css={"screen": ["a.css"], "all": ["c.css", "b.css"]})
        merged = widget1 + widget1
        self.assertEqual(merged._css_lists, [{"screen": ["a.css"], "all": ["b.css"]}])
        self.assertEqual(merged._css, {"screen": ["a.css"], "all": ["b.css"]})
        merged = widget1 + widget2
        self.assertEqual(
            merged._css_lists,
            [
                {"screen": ["a.css"], "all": ["b.css"]},
                {"screen": ["c.css"]},
            ],
        )
        self.assertEqual(merged._css, {"screen": ["a.css", "c.css"], "all": ["b.css"]})
        merged = widget3 + widget4
        # Ordering within lists is preserved.
        self.assertEqual(
            merged._css_lists,
            [
                {"screen": ["a.css"], "all": ["b.css", "c.css"]},
                {"screen": ["a.css"], "all": ["c.css", "b.css"]},
            ],
        )
        msg = (
            "Detected duplicate Media files in an opposite order: "
            "['b.css', 'c.css'], ['c.css', 'b.css']"
        )
        with self.assertWarnsMessage(RuntimeWarning, msg):
            merged._css