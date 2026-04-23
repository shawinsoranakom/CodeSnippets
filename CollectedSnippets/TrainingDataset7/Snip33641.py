def test_for_tag_unpack07(self):
        msg = "'for' tag received an invalid argument: for key,,value in items"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string(
                "for-tag-unpack07", {"items": (("one", 1), ("two", 2))}
            )