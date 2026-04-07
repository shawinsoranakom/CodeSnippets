def test_for_tag_unpack_strs(self):
        output = self.engine.render_to_string(
            "for-tag-unpack-strs", {"items": ("ab", "ac")}
        )
        self.assertEqual(output, "a:b/a:c/")