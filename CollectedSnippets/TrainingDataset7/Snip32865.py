def test_date07(self):
        output = self.engine.render_to_string("date07", {"d": datetime(2009, 3, 12)})
        self.assertEqual(output, "")