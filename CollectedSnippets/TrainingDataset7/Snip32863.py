def test_date05(self):
        output = self.engine.render_to_string("date05", {"d": datetime(2010, 1, 3)})
        self.assertEqual(output, "2009")