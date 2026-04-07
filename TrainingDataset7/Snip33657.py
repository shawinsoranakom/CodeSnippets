def test_for_tag_context(self):
        """
        ForNode.render() pops the values it pushes to the context (#28001).
        """
        output = self.engine.render_to_string(
            "main",
            {
                "alpha": {
                    "values": [("two", 2), ("four", 4)],
                    "extra": [("six", 6), ("eight", 8)],
                },
            },
        )
        self.assertEqual(output, "two:2,four:4,_six:6,eight:8,")