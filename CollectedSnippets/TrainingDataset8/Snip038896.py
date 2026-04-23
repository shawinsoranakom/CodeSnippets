def test_legacy_line_chart_add_rows_with_generic_index(self):
        """Test empty dg._legacy_line_chart with _legacy_add_rows function and a generic index."""
        data = pd.DataFrame([[20, 30, 50]], columns=["a", "b", "c"])
        data.set_index("a", inplace=True)

        chart = st._legacy_line_chart()
        chart._legacy_add_rows(data)

        element = self.get_delta_from_queue().new_element.vega_lite_chart
        chart_spec = json.loads(element.spec)
        self.assertEqual(chart_spec["mark"], "line")
        self.assertEqual(element.datasets[0].data.data.cols[2].int64s.data[0], 30)