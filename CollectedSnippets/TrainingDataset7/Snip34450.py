def test_find_partial_source_fallback_cases(self):
        cases = {"None offsets": (None, None), "Out of bounds offsets": (10, 20)}
        for name, (source_start, source_end) in cases.items():
            with self.subTest(name):
                partial = PartialTemplate(
                    NodeList(),
                    Origin("test"),
                    "test",
                    source_start=source_start,
                    source_end=source_end,
                )
                result = partial.find_partial_source("nonexistent-partial")
                self.assertEqual(result, "")