def test_date06(self):
        output = self.engine.render_to_string(
            "date06",
            {"d": datetime(2009, 3, 12, tzinfo=timezone.get_fixed_timezone(30))},
        )
        self.assertEqual(output, "+0030")