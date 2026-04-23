def test_now04(self):
        output = self.engine.render_to_string("now04")
        self.assertEqual(output, date_format(datetime.now()))