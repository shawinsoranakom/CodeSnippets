def test_truncate_unicode(self):
        self.assertEqual(
            truncatechars_html("<b>\xc5ngstr\xf6m</b> was here", 3), "<b>\xc5n…</b>"
        )