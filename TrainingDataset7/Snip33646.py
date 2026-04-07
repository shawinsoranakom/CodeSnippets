def test_for_tag_unpack09(self):
        """
        A single loopvar doesn't truncate the list in val.
        """
        output = self.engine.render_to_string(
            "for-tag-unpack09", {"items": (("one", 1), ("two", 2))}
        )
        self.assertEqual(output, "one:1/two:2/")