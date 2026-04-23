def test_now06(self):
        output = self.engine.render_to_string("now06")
        self.assertEqual(
            output,
            "%d '%d' %d"
            % (
                datetime.now().day,
                datetime.now().month,
                datetime.now().year,
            ),
        )