def test_theme(self, theme_value, proto_value):
        df = pd.DataFrame(
            {"index": [date(2019, 8, 9), date(2019, 8, 10)], "numbers": [1, 10]}
        ).set_index("index")

        chart = altair._generate_chart(ChartType.LINE, df)
        st._arrow_altair_chart(chart, theme=theme_value)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.arrow_vega_lite_chart.theme, proto_value)