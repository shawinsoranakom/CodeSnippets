def test_now07(self):
        output = self.engine.render_to_string("now07")
        self.assertEqual(
            output,
            "-%d %d %d-"
            % (
                datetime.now().day,
                datetime.now().month,
                datetime.now().year,
            ),
        )