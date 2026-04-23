def test_now05(self):
        output = self.engine.render_to_string("now05")
        self.assertEqual(
            output,
            '%d "%d" %d'
            % (
                datetime.now().day,
                datetime.now().month,
                datetime.now().year,
            ),
        )