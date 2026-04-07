def test_ifchanged_else03(self):
        output = self.engine.render_to_string(
            "ifchanged-else03", {"ids": [1, 1, 2, 2, 2, 3]}
        )
        self.assertEqual(output, "1-red,1,2-blue,2,2,3-red,")