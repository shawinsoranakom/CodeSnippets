def test_date01(self):
        output = self.engine.render_to_string("date01", {"d": datetime(2008, 1, 1)})
        self.assertEqual(output, "01")