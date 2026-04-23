def test_for_tag_unpack05(self):
        output = self.engine.render_to_string(
            "for-tag-unpack05", {"items": (("one", 1), ("two", 2))}
        )
        self.assertEqual(output, "one:1/two:2/")