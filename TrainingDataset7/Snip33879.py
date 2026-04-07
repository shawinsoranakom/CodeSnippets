def test_now02(self):
        output = self.engine.render_to_string("now02")
        self.assertEqual(output, date_format(datetime.now()))