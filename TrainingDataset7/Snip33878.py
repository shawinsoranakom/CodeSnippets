def test_now01(self):
        """
        Simple case
        """
        output = self.engine.render_to_string("now01")
        self.assertEqual(
            output,
            "%d %d %d"
            % (
                datetime.now().day,
                datetime.now().month,
                datetime.now().year,
            ),
        )