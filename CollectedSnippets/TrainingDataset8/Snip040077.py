def test_st_legacy_area_chart(self):
        """Test st._legacy_area_chart."""
        df = pd.DataFrame([[10, 20, 30]], columns=["a", "b", "c"])
        st._legacy_area_chart(df, width=640, height=480)

        el = self.get_delta_from_queue().new_element.vega_lite_chart
        chart_spec = json.loads(el.spec)
        self.assertEqual(chart_spec["mark"], "area")
        self.assertEqual(chart_spec["width"], 640)
        self.assertEqual(chart_spec["height"], 480)
        self.assertEqual(
            el.datasets[0].data.columns.plain_index.data.strings.data,
            ["index", "variable", "value"],
        )

        data = json.loads(json_format.MessageToJson(el.datasets[0].data.data))
        result = [x["int64s"]["data"] for x in data["cols"] if "int64s" in x]
        self.assertEqual(result[1], ["10", "20", "30"])