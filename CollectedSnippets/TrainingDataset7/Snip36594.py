def test_format_string(self):
        self.assertEqual(nformat("1234", "."), "1234")
        self.assertEqual(nformat("1234.2", "."), "1234.2")
        self.assertEqual(nformat("1234", ".", decimal_pos=2), "1234.00")
        self.assertEqual(nformat("1234", ".", grouping=2, thousand_sep=","), "1234")
        self.assertEqual(
            nformat("1234", ".", grouping=2, thousand_sep=",", force_grouping=True),
            "12,34",
        )
        self.assertEqual(nformat("-1234.33", ".", decimal_pos=1), "-1234.3")
        self.assertEqual(
            nformat(
                "10000", ".", grouping=3, thousand_sep="comma", force_grouping=True
            ),
            "10comma000",
        )