def test_ifchanged_filter_ws(self):
        """
        Test whitespace in filter arguments
        """
        output = self.engine.render_to_string("ifchanged-filter-ws", {"num": (1, 2, 3)})
        self.assertEqual(output, "..1..2..3")