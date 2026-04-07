def test_for_tag_unpack04(self):
        output = self.engine.render_to_string(
            "for-tag-unpack04", {"items": (("one", 1), ("two", 2))}
        )
        self.assertEqual(output, "one:1/two:2/")