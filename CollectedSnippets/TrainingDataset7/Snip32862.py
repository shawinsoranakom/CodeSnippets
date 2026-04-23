def test_date04(self):
        output = self.engine.render_to_string("date04", {"d": datetime(2008, 12, 29)})
        self.assertEqual(output, "2009")