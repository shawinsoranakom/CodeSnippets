def test_cycle20(self):
        output = self.engine.render_to_string(
            "cycle20", {"two": "C & D", "one": "A & B"}
        )
        self.assertEqual(output, "A &amp; B &amp; C &amp; D")