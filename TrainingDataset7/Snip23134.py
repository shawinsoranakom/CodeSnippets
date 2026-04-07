def test_add_js_deduplication(self):
        widget1 = Media(js=["a", "b", "c"])
        widget2 = Media(js=["a", "b"])
        widget3 = Media(js=["a", "c", "b"])
        merged = widget1 + widget1
        self.assertEqual(merged._js_lists, [["a", "b", "c"]])
        self.assertEqual(merged._js, ["a", "b", "c"])
        merged = widget1 + widget2
        self.assertEqual(merged._js_lists, [["a", "b", "c"], ["a", "b"]])
        self.assertEqual(merged._js, ["a", "b", "c"])
        # Lists with items in a different order are preserved when added.
        merged = widget1 + widget3
        self.assertEqual(merged._js_lists, [["a", "b", "c"], ["a", "c", "b"]])
        msg = (
            "Detected duplicate Media files in an opposite order: "
            "['a', 'b', 'c'], ['a', 'c', 'b']"
        )
        with self.assertWarnsMessage(RuntimeWarning, msg):
            merged._js