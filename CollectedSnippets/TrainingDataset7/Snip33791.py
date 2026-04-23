def test_ifchanged_else02(self):
        output = self.engine.render_to_string(
            "ifchanged-else02", {"ids": [1, 1, 2, 2, 2, 3]}
        )
        self.assertEqual(output, "1-red,1-gray,2-blue,2-gray,2-gray,3-red,")