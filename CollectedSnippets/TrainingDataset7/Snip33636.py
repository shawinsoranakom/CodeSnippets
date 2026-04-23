def test_for_tag_unpack01(self):
        output = self.engine.render_to_string(
            "for-tag-unpack01", {"items": (("one", 1), ("two", 2))}
        )
        self.assertEqual(output, "one:1/two:2/")