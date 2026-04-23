def test_legacy_area_chart(self):
        """Test dg._legacy_area_chart."""
        data = pd.DataFrame([[20, 30, 50]], columns=["a", "b", "c"])

        st._legacy_area_chart(data)

        element = self.get_delta_from_queue().new_element.vega_lite_chart
        chart_spec = json.loads(element.spec)
        self.assertEqual(chart_spec["mark"], "area")
        self.assertEqual(element.datasets[0].data.data.cols[2].int64s.data[0], 20)