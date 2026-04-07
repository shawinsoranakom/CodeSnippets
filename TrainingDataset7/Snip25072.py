def test_empty_value(self):
        """Empty value must stay empty after being translated (#23196)."""
        with translation.override("de"):
            self.assertEqual("", gettext(""))
            s = mark_safe("")
            self.assertEqual(s, gettext(s))