def test_add07(self):
        output = self.engine.render_to_string(
            "add07", {"d": date(2000, 1, 1), "t": timedelta(10)}
        )
        self.assertEqual(output, "Jan. 11, 2000")