def test_now03(self):
        """
        #15092 - Also accept simple quotes
        """
        output = self.engine.render_to_string("now03")
        self.assertEqual(
            output,
            "%d %d %d"
            % (
                datetime.now().day,
                datetime.now().month,
                datetime.now().year,
            ),
        )