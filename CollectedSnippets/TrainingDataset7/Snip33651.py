def test_for_tag_filter_ws(self):
        """
        #19882
        """
        output = self.engine.render_to_string("for-tag-filter-ws", {"s": "abc"})
        self.assertEqual(output, "abc")