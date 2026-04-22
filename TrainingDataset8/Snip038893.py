def test_date_column_utc_scale(self):
        """Test that columns with date values have UTC time scale"""
        df = pd.DataFrame(
            {"index": [date(2019, 8, 9), date(2019, 8, 10)], "numbers": [1, 10]}
        ).set_index("index")

        chart = altair.generate_chart("line", df)
        st._legacy_altair_chart(chart)
        c = self.get_delta_from_queue().new_element.vega_lite_chart
        spec_dict = json.loads(c.spec)

        # The x axis should have scale="utc", because it uses date values.
        x_scale = _deep_get(spec_dict, "encoding", "x", "scale", "type")
        self.assertEqual(x_scale, "utc")

        # The y axis should _not_ have scale="utc", because it doesn't
        # use date values.
        y_scale = _deep_get(spec_dict, "encoding", "y", "scale", "type")
        self.assertNotEqual(y_scale, "utc")