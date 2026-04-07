def test_cycle21(self):
        output = self.engine.render_to_string(
            "cycle21", {"two": "C & D", "one": "A & B"}
        )
        self.assertEqual(output, "A &amp;amp; B &amp; C &amp;amp; D")