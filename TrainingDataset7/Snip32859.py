def test_date02(self):
        output = self.engine.render_to_string("date02", {"d": datetime(2008, 1, 1)})
        self.assertEqual(output, "Jan. 1, 2008")