def test_ifchanged_else04(self):
        output = self.engine.render_to_string(
            "ifchanged-else04", {"ids": [1, 1, 2, 2, 2, 3, 4]}
        )
        self.assertEqual(output, "***1*1...2***2*3...4...5***3*6***4*7")