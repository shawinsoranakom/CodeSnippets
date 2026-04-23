def test_partial_source_uses_offsets_in_debug(self):
        template = self.engine.get_template("partial_debug_source")
        partial_template = template.extra_data["partials"]["testing-name"]

        self.assertEqual(partial_template._source_start, 0)
        self.assertEqual(partial_template._source_end, 64)
        expected = template.source[
            partial_template._source_start : partial_template._source_end
        ]
        self.assertEqual(partial_template.source, expected)