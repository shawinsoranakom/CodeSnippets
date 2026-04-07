def test_cycle15(self):
        output = self.engine.render_to_string(
            "cycle15", {"test": list(range(5)), "aye": "a", "bee": "b"}
        )
        self.assertEqual(output, "a0,b1,a2,b3,a4,")