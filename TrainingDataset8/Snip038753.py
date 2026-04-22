def test_theme(self, theme_value, proto_value):
        st._arrow_vega_lite_chart(
            df1, {"mark": "rect"}, use_container_width=True, theme=theme_value
        )

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.arrow_vega_lite_chart.theme, proto_value)